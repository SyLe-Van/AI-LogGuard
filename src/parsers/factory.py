"""
Parser factory - automatically detect and select the right parser
"""
from typing import Optional

from .base_parser import BaseParser
from .jenkins_parser import JenkinsParser
from .github_actions_parser import GitHubActionsParser
from ..models.schemas import ParsedLog, Platform


class ParserFactory:
    """Factory for creating the appropriate parser based on log content"""
    
    def __init__(self):
        # Register all available parsers
        self.parsers = [
            JenkinsParser(),
            GitHubActionsParser(),
            # Add more parsers here (GitLab CI, Circle CI, etc.)
        ]
    
    def detect_platform(self, log_content: str) -> Platform:
        """
        Detect which CI/CD platform the log is from
        
        Args:
            log_content: Raw log content
            
        Returns:
            Platform enum value
        """
        for parser in self.parsers:
            if parser.can_parse(log_content):
                return parser.platform
        
        return Platform.UNKNOWN
    
    def get_parser(self, log_content: str) -> Optional[BaseParser]:
        """
        Get the appropriate parser for the log content
        
        Args:
            log_content: Raw log content
            
        Returns:
            Parser instance or None if no parser found
        """
        for parser in self.parsers:
            if parser.can_parse(log_content):
                return parser
        
        return None
    
    def parse(self, log_content: str, **kwargs) -> Optional[ParsedLog]:
        """
        Auto-detect and parse log content
        
        Args:
            log_content: Raw log content
            **kwargs: Additional metadata
            
        Returns:
            ParsedLog object or None if parsing failed
        """
        parser = self.get_parser(log_content)
        
        if parser is None:
            # No parser found - create a basic ParsedLog with unknown platform
            return ParsedLog(
                platform=Platform.UNKNOWN,
                raw_content=log_content,
                total_lines=len(log_content.splitlines()),
            )
        
        return parser.parse(log_content, **kwargs)


# Convenience function for quick parsing
def parse_log(log_content: str, **kwargs) -> Optional[ParsedLog]:
    """
    Quick function to parse any CI/CD log
    
    Args:
        log_content: Raw log content
        **kwargs: Additional metadata (job_name, build_number, etc.)
        
    Returns:
        ParsedLog object
    """
    factory = ParserFactory()
    return factory.parse(log_content, **kwargs)
