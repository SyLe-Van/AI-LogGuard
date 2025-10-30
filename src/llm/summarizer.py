"""
Log Summarizer using LLM
Generates concise, actionable summaries of CI/CD logs
"""
import re
from dataclasses import dataclass
from typing import Optional, List, Union

from .chunker import LogChunker
from . import prompts
from ..models.schemas import ParsedLog
from .gemini_client import GeminiClient


@dataclass
class LogSummary:
    """Structured summary of a log"""
    
    status: str  # Success/Failed/Timeout/Unstable
    main_issue: str  # Primary problem or success message
    key_points: List[str]  # 3-5 bullet points
    impact: str  # Low/Medium/High/Critical
    confidence: int  # 0-100
    raw_response: str  # Full LLM response for debugging


class LogSummarizer:
    """
    AI-powered log summarizer
    
    Uses LLM to generate concise, actionable summaries
    from parsed CI/CD logs
    """
    
    def __init__(
        self,
        client: GeminiClient,  # Now only GeminiClient
        chunker: Optional[LogChunker] = None,
    ):
        """
        Initialize summarizer
        
        Args:
            client: LLM client instance (OpenAI or Ollama)
            chunker: Log chunker (creates one if not provided)
        """
        self.client = client
        self.chunker = chunker or LogChunker()
    
    def summarize(self, parsed_log: ParsedLog) -> LogSummary:
        """
        Generate summary for a parsed log
        
        Args:
            parsed_log: Parsed log object from Phase 1
        
        Returns:
            Structured log summary
        """
        # Build prompt with log data
        prompt = self._build_prompt(parsed_log)
        
        # Get LLM response
        try:
            response = self.client.generate(
                prompt=prompt,
                max_tokens=500,
                system_message=prompts.SYSTEM_MESSAGE,
            )
        except Exception as e:
            # Fallback to basic summary if LLM fails
            return self._fallback_summary(parsed_log, error=str(e))
        
        # Parse response into structured format
        return self._parse_response(response, parsed_log)
    
    def summarize_batch(self, logs: List[ParsedLog]) -> List[LogSummary]:
        """
        Summarize multiple logs
        
        Args:
            logs: List of parsed logs
        
        Returns:
            List of summaries
        """
        summaries = []
        for log in logs:
            summary = self.summarize(log)
            summaries.append(summary)
        return summaries
    
    def _build_prompt(self, parsed_log: ParsedLog) -> str:
        """Build summarization prompt from parsed log"""
        # Prepare log content (truncate if too long)
        log_content = parsed_log.raw_content or ""
        log_size = min(len(log_content), 5000)  # First 5K chars
        
        # Build duration string (duration might not exist in all parsers)
        duration = "Unknown"
        if hasattr(parsed_log, 'duration') and parsed_log.duration:
            duration = f"{parsed_log.duration}s"
        
        # Get platform and status as strings
        platform_str = parsed_log.platform.value if hasattr(parsed_log.platform, 'value') else str(parsed_log.platform)
        status_str = parsed_log.status.value if hasattr(parsed_log.status, 'value') else str(parsed_log.status)
        
        # Use prompt template
        prompt = prompts.build_summarize_prompt(
            platform=platform_str,
            job_name=parsed_log.job_name or "Unknown",
            status=status_str,
            error_count=parsed_log.error_count,
            warning_count=parsed_log.warning_count,
            duration=duration,
            log_content=log_content[:log_size],
            log_size=log_size,
        )
        
        return prompt
    
    def _parse_response(
        self,
        response: str,
        parsed_log: ParsedLog,
    ) -> LogSummary:
        """
        Parse LLM response into structured summary
        
        Args:
            response: Raw LLM response
            parsed_log: Original parsed log
        
        Returns:
            Structured LogSummary
        """
        # Extract sections using regex
        status = self._extract_section(response, r"\*\*STATUS\*\*:?\s*(.+)")
        main_issue = self._extract_section(
            response, r"\*\*MAIN ISSUE\*\*:?\s*(.+)"
        )
        impact = self._extract_section(response, r"\*\*IMPACT\*\*:?\s*(.+)")
        confidence_str = self._extract_section(
            response, r"\*\*CONFIDENCE\*\*:?\s*(\d+)"
        )
        
        # Extract key points (bullet list)
        key_points = self._extract_key_points(response)
        
        # Parse confidence
        try:
            confidence = int(confidence_str) if confidence_str else 75
        except ValueError:
            confidence = 75
        
        # Fallback values if parsing fails
        if not status:
            status = parsed_log.status.value if hasattr(parsed_log.status, 'value') else str(parsed_log.status)
        
        if not main_issue:
            if parsed_log.error_count > 0:
                main_issue = f"Build failed with {parsed_log.error_count} errors"
            else:
                main_issue = "Build completed"
        
        if not impact:
            # Determine impact based on errors
            if parsed_log.error_count > 10:
                impact = "Critical"
            elif parsed_log.error_count > 5:
                impact = "High"
            elif parsed_log.error_count > 0:
                impact = "Medium"
            else:
                impact = "Low"
        
        return LogSummary(
            status=status,
            main_issue=main_issue,
            key_points=key_points or ["No key points extracted"],
            impact=impact,
            confidence=confidence,
            raw_response=response,
        )
    
    def _extract_section(self, text: str, pattern: str) -> str:
        """Extract a section from response using regex"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract bullet points from KEY POINTS section"""
        key_points = []
        
        # Find KEY POINTS section
        match = re.search(
            r"\*\*KEY POINTS\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if match:
            points_text = match.group(1)
            # Extract lines starting with - or •
            lines = points_text.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith(("-", "•", "*")):
                    # Remove bullet and clean
                    point = line.lstrip("-•* ").strip()
                    if point:
                        key_points.append(point)
        
        return key_points
    
    def _fallback_summary(
        self,
        parsed_log: ParsedLog,
        error: Optional[str] = None,
    ) -> LogSummary:
        """
        Generate basic summary without LLM (fallback)
        
        Args:
            parsed_log: Parsed log
            error: Optional error message
        
        Returns:
            Basic summary
        """
        status = parsed_log.status.value if hasattr(parsed_log.status, 'value') else str(parsed_log.status)
        
        # Generate main issue
        if parsed_log.error_count > 0:
            main_issue = (
                f"Build failed with {parsed_log.error_count} error(s) "
                f"and {parsed_log.warning_count} warning(s)"
            )
        elif parsed_log.warning_count > 0:
            main_issue = f"Build completed with {parsed_log.warning_count} warning(s)"
        else:
            main_issue = "Build completed successfully"
        
        # Generate key points from errors
        key_points = []
        
        if parsed_log.errors:
            for error_entry in parsed_log.errors[:3]:  # First 3 errors
                key_points.append(
                    f"Line {error_entry.line_number}: {error_entry.message[:100]}"
                )
        
        if not key_points:
            key_points = ["See full log for details"]
        
        # Determine impact
        if parsed_log.error_count > 10:
            impact = "Critical"
        elif parsed_log.error_count > 5:
            impact = "High"
        elif parsed_log.error_count > 0:
            impact = "Medium"
        else:
            impact = "Low"
        
        return LogSummary(
            status=status,
            main_issue=main_issue,
            key_points=key_points,
            impact=impact,
            confidence=50,  # Low confidence for fallback
            raw_response=f"Fallback summary (LLM error: {error})" if error else "Fallback summary",
        )
