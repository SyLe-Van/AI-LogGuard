"""
Log chunking strategies for handling large logs that exceed LLM context limits
Implements smart chunking with context preservation and priority-based selection
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from ..models.schemas import ParsedLog, LogEntry


# Token estimates (rough approximation: 1 token ≈ 4 characters)
CHARS_PER_TOKEN = 4
GPT_35_TURBO_CONTEXT = 4096  # 4K tokens context window
GPT_4_CONTEXT = 8192  # 8K tokens context window
SAFETY_MARGIN = 0.8  # Use 80% of available context for safety


@dataclass
class LogChunk:
    """Represents a chunk of log content with metadata"""
    content: str
    start_line: int
    end_line: int
    priority: int  # Higher = more important
    token_estimate: int
    has_errors: bool = False
    has_warnings: bool = False
    
    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


class LogChunker:
    """
    Handles chunking of large logs for LLM processing
    
    Strategies:
    1. ERROR_FOCUSED: Prioritize error sections
    2. STAGE_BASED: Chunk by build stages
    3. SEQUENTIAL: Simple sequential chunks
    4. SMART: Combination of strategies based on content
    """
    
    def __init__(self, max_tokens: int = GPT_35_TURBO_CONTEXT):
        """
        Initialize chunker
        
        Args:
            max_tokens: Maximum tokens per chunk
        """
        self.max_tokens = int(max_tokens * SAFETY_MARGIN)
        self.max_chars = self.max_tokens * CHARS_PER_TOKEN
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length"""
        return len(text) // CHARS_PER_TOKEN
    
    def needs_chunking(self, parsed_log: ParsedLog) -> bool:
        """Check if log needs to be chunked"""
        return self.estimate_tokens(parsed_log.raw_content) > self.max_tokens
    
    def chunk_by_errors(self, parsed_log: ParsedLog, context_lines: int = 10) -> List[LogChunk]:
        """
        Chunk log focusing on error sections with context
        
        Args:
            parsed_log: Parsed log to chunk
            context_lines: Lines of context before/after errors
            
        Returns:
            List of chunks prioritizing errors
        """
        if not parsed_log.errors:
            # Fall back to sequential chunking
            return self.chunk_sequential(parsed_log)
        
        chunks = []
        lines = parsed_log.raw_content.splitlines()
        processed_lines = set()
        
        # Create chunks around each error
        for priority, error in enumerate(parsed_log.errors, start=1):
            error_line = error.line_number
            
            # Skip if we've already included this in another chunk
            if error_line in processed_lines:
                continue
            
            # Calculate chunk boundaries
            start = max(0, error_line - context_lines)
            end = min(len(lines), error_line + context_lines)
            
            # Mark lines as processed
            processed_lines.update(range(start, end))
            
            # Extract chunk content
            chunk_lines = lines[start:end]
            content = "\n".join(chunk_lines)
            
            # Check if chunk fits in token limit
            token_estimate = self.estimate_tokens(content)
            if token_estimate > self.max_tokens:
                # If single error chunk is too large, reduce context
                reduced_context = self.max_chars // 2 // len(chunk_lines[0]) if chunk_lines else 5
                start = max(0, error_line - reduced_context)
                end = min(len(lines), error_line + reduced_context)
                chunk_lines = lines[start:end]
                content = "\n".join(chunk_lines)
                token_estimate = self.estimate_tokens(content)
            
            chunks.append(LogChunk(
                content=content,
                start_line=start + 1,  # 1-indexed
                end_line=end,
                priority=len(parsed_log.errors) - priority + 1,  # First error = highest priority
                token_estimate=token_estimate,
                has_errors=True,
                has_warnings=any(w.line_number >= start and w.line_number <= end 
                               for w in parsed_log.warnings)
            ))
        
        # Add a summary chunk with beginning and end if space allows
        if chunks and len(lines) > 100:
            summary_chunk = self._create_summary_chunk(lines)
            if summary_chunk:
                chunks.insert(0, summary_chunk)
        
        return chunks
    
    def chunk_by_stages(self, parsed_log: ParsedLog) -> List[LogChunk]:
        """
        Chunk log by build stages
        
        Args:
            parsed_log: Parsed log with stage information
            
        Returns:
            List of chunks per stage
        """
        if not parsed_log.stages:
            return self.chunk_sequential(parsed_log)
        
        chunks = []
        lines = parsed_log.raw_content.splitlines()
        
        for stage in parsed_log.stages:
            # Extract stage lines
            start = stage.start_line - 1  # Convert to 0-indexed
            end = stage.end_line if stage.end_line else len(lines)
            
            stage_lines = lines[start:end]
            content = "\n".join(stage_lines)
            token_estimate = self.estimate_tokens(content)
            
            # If stage is too large, split it further
            if token_estimate > self.max_tokens:
                sub_chunks = self._split_large_content(content, start + 1)
                chunks.extend(sub_chunks)
            else:
                # Priority: failed stages first, then by order
                priority = 100 if stage.status == "FAILURE" else 50 - len(chunks)
                
                chunks.append(LogChunk(
                    content=content,
                    start_line=start + 1,
                    end_line=end,
                    priority=priority,
                    token_estimate=token_estimate,
                    has_errors=stage.error_count > 0,
                    has_warnings=stage.warning_count > 0
                ))
        
        return chunks
    
    def chunk_sequential(self, parsed_log: ParsedLog) -> List[LogChunk]:
        """
        Simple sequential chunking when no better strategy applies
        
        Args:
            parsed_log: Parsed log to chunk
            
        Returns:
            List of sequential chunks
        """
        content = parsed_log.raw_content
        return self._split_large_content(content, start_line=1)
    
    def chunk_smart(self, parsed_log: ParsedLog) -> List[LogChunk]:
        """
        Smart chunking: choose best strategy based on log content
        
        Priority:
        1. If stages exist and reasonable size: chunk by stages
        2. If many errors: chunk by errors
        3. Otherwise: sequential chunking
        
        Args:
            parsed_log: Parsed log to chunk
            
        Returns:
            List of optimally chunked sections
        """
        # Strategy 1: Stage-based if we have stages
        if parsed_log.stages and len(parsed_log.stages) <= 20:
            return self.chunk_by_stages(parsed_log)
        
        # Strategy 2: Error-focused if we have errors
        if parsed_log.errors:
            return self.chunk_by_errors(parsed_log)
        
        # Strategy 3: Sequential fallback
        return self.chunk_sequential(parsed_log)
    
    def get_priority_chunks(self, 
                           chunks: List[LogChunk], 
                           max_chunks: Optional[int] = None) -> List[LogChunk]:
        """
        Get top priority chunks sorted by importance
        
        Args:
            chunks: List of all chunks
            max_chunks: Maximum number of chunks to return
            
        Returns:
            Sorted list of priority chunks
        """
        sorted_chunks = sorted(chunks, key=lambda c: c.priority, reverse=True)
        
        if max_chunks:
            return sorted_chunks[:max_chunks]
        
        return sorted_chunks
    
    def _split_large_content(self, content: str, start_line: int) -> List[LogChunk]:
        """Split large content into fixed-size chunks"""
        lines = content.splitlines()
        chunks = []
        
        lines_per_chunk = self.max_chars // 100  # Rough estimate
        current_line = start_line
        
        for i in range(0, len(lines), lines_per_chunk):
            chunk_lines = lines[i:i + lines_per_chunk]
            chunk_content = "\n".join(chunk_lines)
            
            chunks.append(LogChunk(
                content=chunk_content,
                start_line=current_line,
                end_line=current_line + len(chunk_lines) - 1,
                priority=len(chunks) + 1,  # Earlier chunks = higher priority
                token_estimate=self.estimate_tokens(chunk_content)
            ))
            
            current_line += len(chunk_lines)
        
        return chunks
    
    def _create_summary_chunk(self, lines: List[str]) -> Optional[LogChunk]:
        """Create a summary chunk with beginning and end of log"""
        summary_size = 50  # Lines from beginning and end
        
        if len(lines) <= summary_size * 2:
            return None
        
        beginning = lines[:summary_size]
        end = lines[-summary_size:]
        
        content = (
            "\n".join(beginning) +
            f"\n\n... ({len(lines) - summary_size * 2} lines omitted) ...\n\n" +
            "\n".join(end)
        )
        
        return LogChunk(
            content=content,
            start_line=1,
            end_line=len(lines),
            priority=5,  # Lower priority than error chunks
            token_estimate=self.estimate_tokens(content)
        )


# Convenience functions
def chunk_log_for_llm(parsed_log: ParsedLog, 
                      strategy: str = "smart",
                      max_tokens: int = GPT_35_TURBO_CONTEXT) -> List[LogChunk]:
    """
    Chunk a parsed log using the specified strategy
    
    Args:
        parsed_log: Parsed log to chunk
        strategy: Chunking strategy (smart, error, stage, sequential)
        max_tokens: Maximum tokens per chunk
        
    Returns:
        List of log chunks
    """
    chunker = LogChunker(max_tokens=max_tokens)
    
    if not chunker.needs_chunking(parsed_log):
        # Return entire log as single chunk
        return [LogChunk(
            content=parsed_log.raw_content,
            start_line=1,
            end_line=parsed_log.total_lines,
            priority=1,
            token_estimate=chunker.estimate_tokens(parsed_log.raw_content),
            has_errors=len(parsed_log.errors) > 0,
            has_warnings=len(parsed_log.warnings) > 0
        )]
    
    strategy_map = {
        "smart": chunker.chunk_smart,
        "error": chunker.chunk_by_errors,
        "stage": chunker.chunk_by_stages,
        "sequential": chunker.chunk_sequential
    }
    
    chunk_func = strategy_map.get(strategy, chunker.chunk_smart)
    return chunk_func(parsed_log)


def estimate_total_tokens(parsed_log: ParsedLog) -> int:
    """Estimate total tokens in a parsed log"""
    return len(parsed_log.raw_content) // CHARS_PER_TOKEN
