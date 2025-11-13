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
        Parse Jenkins pipeline stages with accurate status detection
        
        Returns:
            Dict with 'stages' key containing stage information
        """
        stages: Dict[str, StageInfo] = {}
        stage_order: List[str] = []
        current_stage: Optional[str] = None
        stage_has_errors: Dict[str, bool] = {}  # Track if stage has errors
        stage_skipped: Dict[str, bool] = {}  # Track if stage was skipped
        
        for line in lines:
            # Detect stage start
            stage_match = self.STAGE_START.search(line)
            if stage_match:
                stage_name = stage_match.group(1)
                current_stage = stage_name
                
                if stage_name not in stages:
                    stages[stage_name] = StageInfo(
                        name=stage_name,
                        status=BuildStatus.UNKNOWN,  # Default to UNKNOWN, will be determined later
                    )
                    stage_order.append(stage_name)
                    stage_has_errors[stage_name] = False
                    stage_skipped[stage_name] = False
            
            # ✅ IMPROVED: Detect stage skipped BEFORE checking errors
            if current_stage and current_stage in stages:
                line_lower = line.lower()
                
                # Pattern 0: Stage was skipped (highest priority - ignore this stage)
                if 'stage skipped due to' in line_lower or 'skipped due to earlier failure' in line_lower:
                    stage_skipped[current_stage] = True
                    # Don't override FAILED status, but mark as skipped
                    if stages[current_stage].status != BuildStatus.FAILED:
                        stages[current_stage].status = BuildStatus.UNKNOWN
                    continue  # Skip checking other patterns for skipped stages
                
                # Only check error patterns if stage was NOT skipped
                if not stage_skipped.get(current_stage, False):
                    # Pattern 1: Explicit FAILED/FAILURE marker
                    if 'failed' in line_lower or 'failure' in line_lower:
                        stages[current_stage].status = BuildStatus.FAILED
                        stage_has_errors[current_stage] = True
                    
                    # Pattern 2: Exit code 127 (command not found)
                    elif 'exit code 127' in line_lower or 'script returned exit code 127' in line_lower:
                        stages[current_stage].status = BuildStatus.FAILED
                        stage_has_errors[current_stage] = True
                    
                    # Pattern 3: Other non-zero exit codes
                    elif re.search(r'exit code [1-9]\d*', line_lower) or re.search(r'script returned exit code [1-9]\d*', line_lower):
                        # Only mark as failed if it's a non-zero exit code
                        if 'exit code 0' not in line_lower:
                            stages[current_stage].status = BuildStatus.FAILED
                            stage_has_errors[current_stage] = True
                    
                    # Pattern 4: Docker/command not found errors
                    elif ('docker: not found' in line_lower or 
                          'node: not found' in line_lower or 
                          'python: not found' in line_lower or
                          'command not found' in line_lower):
                        stages[current_stage].status = BuildStatus.FAILED
                        stage_has_errors[current_stage] = True
                    
                    # Pattern 5: Permission denied
                    elif 'permission denied' in line_lower:
                        stages[current_stage].status = BuildStatus.FAILED
                        stage_has_errors[current_stage] = True
        
        # Final pass: Set remaining UNKNOWN stages to SUCCESS if they have no errors and weren't skipped
        for stage_name in stages:
            if stages[stage_name].status == BuildStatus.UNKNOWN:
                # If stage was skipped, keep as UNKNOWN
                if stage_skipped.get(stage_name, False):
                    stages[stage_name].status = BuildStatus.UNKNOWN
                # If stage has no explicit failure markers and wasn't skipped, consider it SUCCESS
                elif not stage_has_errors.get(stage_name, False):
                    stages[stage_name].status = BuildStatus.SUCCESS
                else:
                    # Has errors but no explicit FAILED marker
                    stages[stage_name].status = BuildStatus.FAILED
        
        return {
            'stages': stages,
            'order': stage_order
        }
