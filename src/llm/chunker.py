"""
Log chunking strategy for handling large logs
Splits logs intelligently to fit within token limits
"""
from typing import List, Optional

from ..models.schemas import ParsedLog, LogEntry


class LogChunker:
    """
    Smart log chunker that splits large logs while preserving context
    
    Strategy:
    1. Extract high-priority sections (errors, warnings)
    2. Chunk remaining content
    3. Maintain overlap between chunks
    4. Stay within token limits
    """
    
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        max_tokens: int = 3000,
        overlap_tokens: int = 100,
        client=None,  # Optional GeminiClient for accurate token counting
    ):
        """
        Initialize log chunker
        
        Args:
            model: Model name (for reference)
            max_tokens: Maximum tokens per chunk (safe limit)
            overlap_tokens: Overlap between chunks for context
            client: Optional GeminiClient for accurate token counting
        """
        self.model = model
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.client = client
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Input text
        
        Returns:
            Number of tokens
        """
        # Use client if available for accurate counting
        if self.client and hasattr(self.client, 'count_tokens'):
            try:
                return self.client.count_tokens(text)
            except:
                pass
        
        # Fallback: rough estimate (1 token ≈ 4 chars for most models)
        return len(text) // 4
    
    def chunk_log(
        self,
        parsed_log: ParsedLog,
        prioritize_errors: bool = True,
    ) -> List[str]:
        """
        Chunk log into manageable pieces
        
        Args:
            parsed_log: Parsed log object
            prioritize_errors: Extract error sections first
        
        Returns:
            List of log chunks (strings)
        """
        chunks = []
        
        # Build metadata section (always first)
        metadata = self._build_metadata_section(parsed_log)
        
        # Build error section (high priority)
        if prioritize_errors and parsed_log.errors:
            error_section = self._build_error_section(parsed_log)
            chunks.append(f"{metadata}\n\n{error_section}")
        else:
            chunks.append(metadata)
        
        # Check if remaining content needs chunking
        remaining_content = parsed_log.raw_content or ""
        remaining_tokens = self.count_tokens(remaining_content)
        
        if remaining_tokens <= self.max_tokens:
            # Fits in one chunk - combine with metadata
            if len(chunks) == 1 and remaining_content:
                chunks[0] = f"{chunks[0]}\n\n{remaining_content}"
        else:
            # Split remaining content
            content_chunks = self._split_content(
                remaining_content,
                exclude_lines=self._get_error_lines(parsed_log),
            )
            chunks.extend(content_chunks)
        
        return chunks
    
    def _build_metadata_section(self, parsed_log: ParsedLog) -> str:
        """Build metadata section with key info"""
        lines = [
            "=== BUILD METADATA ===",
            f"Platform: {parsed_log.platform.value}",
            f"Job: {parsed_log.job_name or 'Unknown'}",
            f"Build: {parsed_log.build_number or 'N/A'}",
            f"Status: {parsed_log.status.value}",
            f"Errors: {parsed_log.error_count}",
            f"Warnings: {parsed_log.warning_count}",
        ]
        
        if parsed_log.triggered_by:
            lines.append(f"Triggered by: {parsed_log.triggered_by}")
        
        # Duration might not exist in all parsers
        if hasattr(parsed_log, 'duration') and parsed_log.duration:
            lines.append(f"Duration: {parsed_log.duration}s")
        
        # Add stage summary
        if parsed_log.stages:
            lines.append(f"\nStages: {len(parsed_log.stages)}")
            for stage in parsed_log.stages[:5]:  # First 5 stages
                status_icon = "✅" if stage.status.value == "SUCCESS" else "❌"
                lines.append(f"  {status_icon} {stage.name} - {stage.status.value}")
            
            if len(parsed_log.stages) > 5:
                lines.append(f"  ... and {len(parsed_log.stages) - 5} more")
        
        return "\n".join(lines)
    
    def _build_error_section(self, parsed_log: ParsedLog) -> str:
        """Build section with errors and warnings"""
        lines = ["\n=== ERRORS & WARNINGS ===\n"]
        
        # Add errors
        if parsed_log.errors:
            lines.append(f"Errors ({len(parsed_log.errors)}):")
            for i, error in enumerate(parsed_log.errors[:10], 1):  # Max 10 errors
                lines.append(
                    f"\n{i}. [{error.level.value}] Line {error.line_number}:"
                )
                lines.append(f"   {error.message}")
            
            if len(parsed_log.errors) > 10:
                lines.append(f"\n... and {len(parsed_log.errors) - 10} more errors")
        
        # Add warnings
        if parsed_log.warnings:
            lines.append(f"\nWarnings ({len(parsed_log.warnings)}):")
            for i, warning in enumerate(parsed_log.warnings[:5], 1):  # Max 5 warnings
                lines.append(f"\n{i}. Line {warning.line_number}:")
                lines.append(f"   {warning.message}")
            
            if len(parsed_log.warnings) > 5:
                lines.append(
                    f"\n... and {len(parsed_log.warnings) - 5} more warnings"
                )
        
        return "\n".join(lines)
    
    def _get_error_lines(self, parsed_log: ParsedLog) -> set:
        """Get line numbers of errors to avoid duplication"""
        error_lines = set()
        
        if parsed_log.errors:
            error_lines.update(e.line_number for e in parsed_log.errors)
        
        return error_lines
    
    def _split_content(
        self,
        content: str,
        exclude_lines: Optional[set] = None,
    ) -> List[str]:
        """
        Split content into chunks with overlap
        
        Args:
            content: Full content to split
            exclude_lines: Line numbers to exclude (already in error section)
        
        Returns:
            List of content chunks
        """
        exclude_lines = exclude_lines or set()
        lines = content.split("\n")
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for line_num, line in enumerate(lines, 1):
            # Skip lines already in error section
            if line_num in exclude_lines:
                continue
            
            line_tokens = self.count_tokens(line)
            
            # Check if adding this line exceeds limit
            if current_tokens + line_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunks.append("\n".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_lines = current_chunk[-10:]  # Last 10 lines
                current_chunk = overlap_lines + [line]
                current_tokens = sum(
                    self.count_tokens(l) for l in current_chunk
                )
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks
    
    def estimate_chunks(self, parsed_log: ParsedLog) -> int:
        """
        Estimate number of chunks without actually splitting
        
        Args:
            parsed_log: Parsed log object
        
        Returns:
            Estimated number of chunks
        """
        total_tokens = self.count_tokens(parsed_log.raw_content or "")
        return max(1, (total_tokens + self.max_tokens - 1) // self.max_tokens)
