"""
GitHub Actions log parser
Parses GitHub Actions workflow logs into unified ParsedLog structure
"""
import re
from typing import Optional, Dict, List

from .base_parser import BaseParser
from ..models.schemas import (
    ParsedLog,
    LogEntry,
    StageInfo,
    LogLevel,
    BuildStatus,
    Platform,
)


class GitHubActionsParser(BaseParser):
    """Parser for GitHub Actions workflow logs"""
    
    # GitHub Actions-specific patterns
    GROUP_START = re.compile(r'##\[group\](.+)')
    GROUP_END = re.compile(r'##\[endgroup\]')
    ANNOTATION_ERROR = re.compile(r'::error::(.+)')
    ANNOTATION_WARNING = re.compile(r'::warning::(.+)')
    ANNOTATION_DEBUG = re.compile(r'::debug::(.+)')
    SET_OUTPUT = re.compile(r'::set-output name=(.+)::(.+)')
    STEP_START = re.compile(r'##\[command\](.+)')
    
    def __init__(self):
        super().__init__()
        self.platform = Platform.GITHUB_ACTIONS
    
    def can_parse(self, log_content: str) -> bool:
        """Check if this is a GitHub Actions log"""
        gh_actions_markers = [
            '##[group]',
            '::error::',
            '::warning::',
            'github.com',
            'actions/',
            '##[command]',
        ]
        return any(marker in log_content for marker in gh_actions_markers)
    
    def parse(self, log_content: str, **kwargs) -> ParsedLog:
        """
        Parse GitHub Actions workflow log
        
        Args:
            log_content: Raw GitHub Actions log output
            **kwargs: job_name, workflow_name, run_id, branch, commit
            
        Returns:
            ParsedLog object
        """
        lines = log_content.splitlines()
        
        # Initialize parsed log
        parsed = ParsedLog(
            platform=Platform.GITHUB_ACTIONS,
            job_name=kwargs.get('job_name') or kwargs.get('workflow_name'),
            build_number=kwargs.get('run_id'),
            build_url=kwargs.get('build_url'),
            branch=kwargs.get('branch'),
            commit=kwargs.get('commit'),
            raw_content=log_content,
            total_lines=len(lines),
        )
        
        # Parse steps (equivalent to stages)
        step_data = self._parse_steps(lines)
        parsed.stages = list(step_data['steps'].values())
        
        # Parse errors, warnings, and collect log entries
        errors: List[LogEntry] = []
        warnings: List[LogEntry] = []
        retry_count = 0
        
        current_step: Optional[str] = None
        
        for line_num, line in enumerate(lines, start=1):
            # Track current step
            cmd_match = self.STEP_START.search(line)
            if cmd_match:
                current_step = cmd_match.group(1)[:50]  # Truncate long commands
            
            # GitHub Actions annotations (high priority)
            error_annotation = self.ANNOTATION_ERROR.search(line)
            if error_annotation:
                log_entry = LogEntry(
                    level=LogLevel.ERROR,
                    message=error_annotation.group(1),
                    line_number=line_num,
                    raw_line=line
                )
                errors.append(log_entry)
                
                if current_step and current_step in step_data['steps']:
                    step_data['steps'][current_step].error_count += 1
                continue
            
            warning_annotation = self.ANNOTATION_WARNING.search(line)
            if warning_annotation:
                log_entry = LogEntry(
                    level=LogLevel.WARNING,
                    message=warning_annotation.group(1),
                    line_number=line_num,
                    raw_line=line
                )
                warnings.append(log_entry)
                
                if current_step and current_step in step_data['steps']:
                    step_data['steps'][current_step].warning_count += 1
                continue
            
            # Detect retries
            if self.is_retry_line(line):
                retry_count += 1
                if current_step and current_step in step_data['steps']:
                    step_data['steps'][current_step].retry_count += 1
            
            # Regular error detection
            if self.is_error_line(line):
                log_entry = self.create_log_entry(line, line_num, LogLevel.ERROR)
                errors.append(log_entry)
                
                if current_step and current_step in step_data['steps']:
                    step_data['steps'][current_step].error_count += 1
            
            # Regular warning detection
            elif self.is_warning_line(line):
                log_entry = self.create_log_entry(line, line_num, LogLevel.WARNING)
                warnings.append(log_entry)
                
                if current_step and current_step in step_data['steps']:
                    step_data['steps'][current_step].warning_count += 1
        
        # Update parsed log
        parsed.errors = errors
        parsed.warnings = warnings
        parsed.error_count = len(errors)
        parsed.warning_count = len(warnings)
        parsed.retry_count = retry_count
        parsed.stages = list(step_data['steps'].values())
        
        # Determine status
        parsed.status = self._determine_status(parsed, log_content)
        
        return parsed
    
    def _parse_steps(self, lines: List[str]) -> Dict:
        """
        Parse GitHub Actions steps (similar to Jenkins stages)
        
        Returns:
            Dict with 'steps' key containing step information
        """
        steps: Dict[str, StageInfo] = {}
        step_order: List[str] = []
        current_group: Optional[str] = None
        
        for line in lines:
            # Detect group start (represents a step)
            group_match = self.GROUP_START.search(line)
            if group_match:
                step_name = group_match.group(1).strip()
                current_group = step_name
                
                if step_name not in steps:
                    steps[step_name] = StageInfo(
                        name=step_name,
                        status=BuildStatus.SUCCESS,
                    )
                    step_order.append(step_name)
            
            # Mark step as failed if contains failure indicators
            if current_group and (
                'Error:' in line or 
                'FAILED' in line or 
                'Process completed with exit code' in line
            ):
                if '0' not in line:  # Exit code 0 is success
                    steps[current_group].status = BuildStatus.FAILED
        
        return {
            'steps': steps,
            'order': step_order
        }
    
    def _determine_status(self, parsed: ParsedLog, log_content: str) -> BuildStatus:
        """Determine final build status"""
        # Check for explicit status in log
        if 'Completed successfully' in log_content or 'Process completed with exit code 0' in log_content:
            return BuildStatus.SUCCESS
        
        # Check for failures
        if parsed.error_count > 0 or any(s.status == BuildStatus.FAILED for s in parsed.stages):
            return BuildStatus.FAILED
        
        # Check for warnings
        if parsed.warning_count > 0:
            return BuildStatus.UNSTABLE
        
        return BuildStatus.SUCCESS
