"""
LLM-powered log summarizer
Generates intelligent summaries of CI/CD build logs using OpenAI
"""
from typing import Dict, List, Optional
import logging
from ..models.schemas import ParsedLog, BuildStatus
from .openai_client import get_openai_client
from .prompts import (
    SYSTEM_PROMPT_EXPERT,
    SUMMARIZE_LOG_PROMPT,
    SUMMARIZE_LOG_WITH_STAGES_PROMPT,
    format_log_for_prompt,
    format_stages_info,
    format_errors_summary
)
from .chunker import chunk_log_for_llm, estimate_total_tokens, GPT_35_TURBO_CONTEXT


logger = logging.getLogger(__name__)


class LogSummarizer:
    """
    Generates intelligent summaries of parsed CI/CD logs using LLM
    
    Features:
    - Automatic chunking for large logs
    - Stage-aware summarization
    - Error-focused summaries
    - Token usage tracking
    """
    
    def __init__(self, 
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.3,
                 max_tokens: int = 500):
        """
        Initialize summarizer
        
        Args:
            model: OpenAI model to use
            temperature: Sampling temperature (lower = more focused)
            max_tokens: Maximum tokens in response
        """
        self.client = get_openai_client()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def summarize(self, parsed_log: ParsedLog) -> Dict[str, any]:
        """
        Generate a comprehensive summary of the parsed log
        
        Args:
            parsed_log: Parsed log to summarize
            
        Returns:
            Dictionary with:
            - summary: Text summary
            - tokens_used: Total tokens consumed
            - model: Model used
            - chunks_processed: Number of chunks (if chunked)
        """
        # Check if log needs chunking
        total_tokens = estimate_total_tokens(parsed_log)
        logger.info(f"Log estimated at {total_tokens} tokens")
        
        if total_tokens > GPT_35_TURBO_CONTEXT * 0.6:  # Leave room for prompt + response
            logger.info("Log exceeds token limit, using chunking strategy")
            return self._summarize_chunked(parsed_log)
        else:
            logger.info("Log fits in context, generating direct summary")
            return self._summarize_direct(parsed_log)
    
    def _summarize_direct(self, parsed_log: ParsedLog) -> Dict[str, any]:
        """Summarize log that fits in single LLM call"""
        # Choose appropriate prompt based on log structure
        if parsed_log.stages:
            prompt = self._build_stages_prompt(parsed_log)
        else:
            prompt = self._build_simple_prompt(parsed_log)
        
        # Call LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_EXPERT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat_completion(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return {
            "summary": response["content"],
            "tokens_used": response["tokens"],
            "model": response["model"],
            "chunks_processed": 1,
            "strategy": "direct"
        }
    
    def _summarize_chunked(self, parsed_log: ParsedLog) -> Dict[str, any]:
        """Summarize large log using chunking strategy"""
        # Chunk the log
        chunks = chunk_log_for_llm(parsed_log, strategy="smart")
        logger.info(f"Log split into {len(chunks)} chunks")
        
        # Summarize priority chunks (top 3 for now)
        priority_chunks = sorted(chunks, key=lambda c: c.priority, reverse=True)[:3]
        
        chunk_summaries = []
        total_tokens = 0
        
        for i, chunk in enumerate(priority_chunks, 1):
            logger.info(f"Summarizing chunk {i}/{len(priority_chunks)} "
                       f"(lines {chunk.start_line}-{chunk.end_line})")
            
            prompt = self._build_chunk_prompt(chunk, parsed_log)
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_EXPERT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=300  # Shorter summaries per chunk
            )
            
            chunk_summaries.append({
                "lines": f"{chunk.start_line}-{chunk.end_line}",
                "summary": response["content"],
                "has_errors": chunk.has_errors
            })
            
            total_tokens += response["tokens"]
        
        # Combine chunk summaries into final summary
        final_summary = self._combine_chunk_summaries(
            parsed_log, 
            chunk_summaries
        )
        
        return {
            "summary": final_summary,
            "tokens_used": total_tokens,
            "model": self.model,
            "chunks_processed": len(priority_chunks),
            "strategy": "chunked"
        }
    
    def _build_simple_prompt(self, parsed_log: ParsedLog) -> str:
        """Build prompt for simple log without stages"""
        log_content = format_log_for_prompt(parsed_log, max_lines=100)
        
        return SUMMARIZE_LOG_PROMPT.format(
            platform=parsed_log.platform.value,
            status=parsed_log.status.value,
            total_lines=parsed_log.total_lines,
            error_count=len(parsed_log.errors),
            warning_count=len(parsed_log.warnings),
            log_content=log_content
        )
    
    def _build_stages_prompt(self, parsed_log: ParsedLog) -> str:
        """Build prompt for log with stages"""
        stages_info = format_stages_info(parsed_log)
        errors_summary = format_errors_summary(parsed_log)
        
        return SUMMARIZE_LOG_WITH_STAGES_PROMPT.format(
            platform=parsed_log.platform.value,
            status=parsed_log.status.value,
            stage_count=len(parsed_log.stages),
            error_count=len(parsed_log.errors),
            warning_count=len(parsed_log.warnings),
            stages_info=stages_info,
            errors_summary=errors_summary
        )
    
    def _build_chunk_prompt(self, chunk, parsed_log: ParsedLog) -> str:
        """Build prompt for a specific chunk"""
        context = f"This is part of a larger {parsed_log.platform.value} build log."
        if chunk.has_errors:
            context += " This section contains critical errors."
        
        return f"""{context}

**Log Section (Lines {chunk.start_line}-{chunk.end_line}):**
{chunk.content}

**Task:** Provide a concise summary focusing on what went wrong and why."""
    
    def _combine_chunk_summaries(self, 
                                 parsed_log: ParsedLog, 
                                 chunk_summaries: List[Dict]) -> str:
        """Combine multiple chunk summaries into cohesive final summary"""
        parts = [
            f"# Build Summary: {parsed_log.status.value}",
            f"Platform: {parsed_log.platform.value}",
            f"Total: {parsed_log.total_lines} lines, "
            f"{len(parsed_log.errors)} errors, "
            f"{len(parsed_log.warnings)} warnings",
            ""
        ]
        
        # Add stage overview if available
        if parsed_log.stages:
            failed_stages = [s for s in parsed_log.stages if s.status == "FAILURE"]
            if failed_stages:
                parts.append(f"**Failed Stages:** {', '.join(s.name for s in failed_stages)}")
                parts.append("")
        
        # Add chunk summaries
        parts.append("## Key Issues")
        for i, chunk_summary in enumerate(chunk_summaries, 1):
            prefix = "🔴" if chunk_summary["has_errors"] else "ℹ️"
            parts.append(f"{prefix} **Section {i}** (Lines {chunk_summary['lines']}):")
            parts.append(chunk_summary["summary"])
            parts.append("")
        
        return "\n".join(parts)
    
    def quick_summary(self, parsed_log: ParsedLog) -> str:
        """
        Generate a quick one-sentence summary
        
        Args:
            parsed_log: Parsed log
            
        Returns:
            Brief summary string
        """
        status = parsed_log.status.value
        platform = parsed_log.platform.value
        error_count = len(parsed_log.errors)
        warning_count = len(parsed_log.warnings)
        
        if parsed_log.status == BuildStatus.SUCCESS:
            return f"✅ {platform} build succeeded with {warning_count} warnings"
        elif parsed_log.status == BuildStatus.FAILED:
            return f"❌ {platform} build failed with {error_count} errors and {warning_count} warnings"
        else:
            return f"⚠️ {platform} build unstable with {error_count} errors and {warning_count} warnings"


# Convenience function
def summarize_log(parsed_log: ParsedLog, 
                 model: str = "gpt-3.5-turbo",
                 use_llm: bool = True) -> Dict[str, any]:
    """
    Summarize a parsed log
    
    Args:
        parsed_log: Parsed log to summarize
        model: OpenAI model to use
        use_llm: Whether to use LLM (False = simple summary only)
        
    Returns:
        Summary dictionary
    """
    summarizer = LogSummarizer(model=model)
    
    if not use_llm:
        # Return simple summary without LLM
        return {
            "summary": summarizer.quick_summary(parsed_log),
            "tokens_used": 0,
            "model": None,
            "strategy": "quick"
        }
    
    return summarizer.summarize(parsed_log)
