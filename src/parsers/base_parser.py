"""
Base parser interface for all CI/CD log parsers
"""
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ..models.schemas import (
    ParsedLog,
    LogEntry,
    StageInfo,
    LogLevel,
    BuildStatus,
    Platform,
)


class BaseParser(ABC):
    """Base class for all log parsers"""
    
    # Common regex patterns
    ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')
    TIMESTAMP_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}')
    
    def __init__(self):
        self.platform = Platform.UNKNOWN
    
    @abstractmethod
    def can_parse(self, log_content: str) -> bool:
        """
        Determine if this parser can handle the given log content
        
        Args:
            log_content: Raw log content as string
            
        Returns:
            True if this parser can handle the log
        """
        pass
    
    @abstractmethod
    def parse(self, log_content: str, **kwargs) -> ParsedLog:
        """
        Parse log content into unified ParsedLog structure
        
        Args:
            log_content: Raw log content as string
            **kwargs: Additional metadata (job_name, build_number, etc.)
            
        Returns:
            ParsedLog object with parsed information
        """
        pass
    
    def clean_ansi(self, text: str) -> str:
        """Remove ANSI escape codes from text"""
        return self.ANSI_ESCAPE.sub('', text)
    
    def clean_line(self, line: str) -> str:
        """
        Clean a log line:
        - Remove ANSI codes
        - Strip whitespace
        - Remove echo prefixes
        """
        line = self.clean_ansi(line)
        line = re.sub(r'^\+ echo ', '', line)
        return line.strip()
    
    def detect_log_level(self, line: str) -> LogLevel:
        """Detect log level from line content"""
        line_upper = line.upper()
        
        if any(keyword in line_upper for keyword in ['CRITICAL', '2 CRITICAL ERRORS']):
            return LogLevel.CRITICAL
        elif any(keyword in line_upper for keyword in ['[ERROR]', 'ERROR:', 'FAILED', 'FAILURE']):
            return LogLevel.ERROR
        elif any(keyword in line_upper for keyword in ['[WARNING]', 'WARNING:', 'WARN:']):
            return LogLevel.WARNING
        elif any(keyword in line_upper for keyword in ['[DEBUG]', 'DEBUG:']):
            return LogLevel.DEBUG
        else:
            return LogLevel.INFO
    
    def is_error_line(self, line: str) -> bool:
        """Check if a line contains an error"""
        error_patterns = [
            r'\[ERROR\]',
            r'\bERROR\b',
            r'\bFAILED\b',
            r'\bFAILURE\b',
            r'compilation failed',
            r'test.*failed',
            r'dependency.*error',
            r'timeout',
            r'exception',
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in error_patterns)
    
    def is_warning_line(self, line: str) -> bool:
        """Check if a line contains a warning"""
        warning_patterns = [
            r'\[WARNING\]',
            r'\bWARNING\b',
            r'\bWARN\b',
            r'deprecated',
            r'unstable',
            r'flaky',
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in warning_patterns)
    
    def is_retry_line(self, line: str) -> bool:
        """Check if a line indicates a retry"""
        retry_patterns = [
            r'\bretry',
            r'\bretried',
            r're-try',
            r'try again',
            r'attempting again',
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in retry_patterns)
    
    def extract_build_status(self, log_content: str) -> BuildStatus:
        """Extract final build status from log"""
        # Look for common status indicators
        if re.search(r'Finished: SUCCESS', log_content, re.IGNORECASE):
            return BuildStatus.SUCCESS
        elif re.search(r'Finished: FAILURE|BUILD FAILED', log_content, re.IGNORECASE):
            return BuildStatus.FAILED
        elif re.search(r'Finished: UNSTABLE', log_content, re.IGNORECASE):
            return BuildStatus.UNSTABLE
        elif re.search(r'TIMEOUT|TIMED OUT', log_content, re.IGNORECASE):
            return BuildStatus.TIMEOUT
        elif re.search(r'ABORTED|CANCELLED', log_content, re.IGNORECASE):
            return BuildStatus.ABORTED
        
        return BuildStatus.UNKNOWN
    
    def create_log_entry(
        self,
        line: str,
        line_number: int,
        level: Optional[LogLevel] = None
    ) -> LogEntry:
        """Create a LogEntry from a line"""
        if level is None:
            level = self.detect_log_level(line)
        
        message = self.clean_line(line)
        
        return LogEntry(
            level=level,
            message=message,
            line_number=line_number,
            raw_line=line
        )
