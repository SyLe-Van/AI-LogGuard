"""
Jenkins log parser
Parses Jenkins console output into unified ParsedLog structure
"""
import re
from typing import Optional, Dict, List
from collections import defaultdict

from .base_parser import BaseParser
from ..models.schemas import (
    ParsedLog,
    LogEntry,
    StageInfo,
    LogLevel,
    BuildStatus,
    Platform,
)


class JenkinsParser(BaseParser):
    """Parser for Jenkins console logs"""
    
    # Jenkins-specific patterns
    STAGE_START = re.compile(r'\[Pipeline\] \{ \(([^)]+)\)')
    STAGE_END = re.compile(r'\[Pipeline\] \}')
    STATUS_LINE = re.compile(r'Finished: (SUCCESS|FAILURE|UNSTABLE|ABORTED)', re.IGNORECASE)
    STARTED_BY = re.compile(r'Started by (.+)')
    DURATION = re.compile(r'Duration: (\d+) (sec|min|hr)')
    
    def __init__(self):
        super().__init__()
        self.platform = Platform.JENKINS
    
    def can_parse(self, log_content: str) -> bool:
        """Check if this is a Jenkins log"""
        jenkins_markers = [
            '[Pipeline]',
            'Running on Jenkins',
            'Started by user',
            '/var/jenkins_home/',
        ]
        return any(marker in log_content for marker in jenkins_markers)
    
    def parse(self, log_content: str, **kwargs) -> ParsedLog:
        """
        Parse Jenkins console log
        
        Args:
            log_content: Raw Jenkins console output
            **kwargs: job_name, build_number, build_url
            
        Returns:
            ParsedLog object
        """
        lines = log_content.splitlines()
        
        # Initialize parsed log
        parsed = ParsedLog(
            platform=Platform.JENKINS,
            job_name=kwargs.get('job_name'),
            build_number=kwargs.get('build_number'),
            build_url=kwargs.get('build_url'),
            raw_content=log_content,
            total_lines=len(lines),
        )
        
        # Extract metadata
        parsed.status = self.extract_build_status(log_content)
        parsed.triggered_by = self._extract_triggered_by(log_content)
        parsed.duration_seconds = self._extract_duration(log_content)
        
        # Parse stages and content
        stage_data = self._parse_stages(lines)
        parsed.stages = list(stage_data['stages'].values())
        
        # Parse errors, warnings, and build log entries
        errors: List[LogEntry] = []
        warnings: List[LogEntry] = []
        retry_count = 0
        
        current_stage: Optional[str] = None
        
        for line_num, line in enumerate(lines, start=1):
            # Skip echo lines
            if line.strip().startswith('+ echo'):
                continue
            
            # Track current stage
            stage_match = self.STAGE_START.search(line)
            if stage_match:
                current_stage = stage_match.group(1)
            
            # Detect retries
            if self.is_retry_line(line):
                retry_count += 1
                if current_stage and current_stage in stage_data['stages']:
                    stage_data['stages'][current_stage].retry_count += 1
            
            # Collect errors
            if self.is_error_line(line):
                log_entry = self.create_log_entry(line, line_num, LogLevel.ERROR)
                errors.append(log_entry)
                
                if current_stage and current_stage in stage_data['stages']:
                    stage_data['stages'][current_stage].error_count += 1
                    
                    # Check for critical
                    if 'critical' in line.lower():
                        stage_data['stages'][current_stage].critical_count += 1
                        log_entry.level = LogLevel.CRITICAL
            
            # Collect warnings
            elif self.is_warning_line(line):
                log_entry = self.create_log_entry(line, line_num, LogLevel.WARNING)
                warnings.append(log_entry)
                
                if current_stage and current_stage in stage_data['stages']:
                    stage_data['stages'][current_stage].warning_count += 1
        
        # Update parsed log with collected data
        parsed.errors = errors
        parsed.warnings = warnings
        parsed.error_count = len(errors)
        parsed.warning_count = len(warnings)
        parsed.retry_count = retry_count
        parsed.stages = list(stage_data['stages'].values())
        
        # Determine final status if not already set
        if parsed.status == BuildStatus.UNKNOWN:
            if parsed.error_count > 0:
                parsed.status = BuildStatus.FAILED
            elif parsed.warning_count > 0:
                parsed.status = BuildStatus.UNSTABLE
            else:
                parsed.status = BuildStatus.SUCCESS
        
        return parsed
    
    def _extract_triggered_by(self, log_content: str) -> Optional[str]:
        """Extract who triggered the build"""
        match = self.STARTED_BY.search(log_content)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_duration(self, log_content: str) -> Optional[float]:
        """Extract build duration in seconds"""
        match = self.DURATION.search(log_content)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'sec':
                return float(value)
            elif unit == 'min':
                return float(value * 60)
            elif unit == 'hr':
                return float(value * 3600)
        
        return None
    
    def _parse_stages(self, lines: List[str]) -> Dict:
        """
        Parse Jenkins pipeline stages
        
        Returns:
            Dict with 'stages' key containing stage information
        """
        stages: Dict[str, StageInfo] = {}
        stage_order: List[str] = []
        current_stage: Optional[str] = None
        
        for line in lines:
            # Detect stage start
            stage_match = self.STAGE_START.search(line)
            if stage_match:
                stage_name = stage_match.group(1)
                current_stage = stage_name
                
                if stage_name not in stages:
                    stages[stage_name] = StageInfo(
                        name=stage_name,
                        status=BuildStatus.SUCCESS,  # Default to success
                    )
                    stage_order.append(stage_name)
            
            # Detect stage failures
            if current_stage and ('FAILED' in line or 'FAILURE' in line):
                stages[current_stage].status = BuildStatus.FAILED
        
        return {
            'stages': stages,
            'order': stage_order
        }
