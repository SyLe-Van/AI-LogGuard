"""
Fix Suggester using LLM
Generates actionable fix suggestions for CI/CD build errors
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from . import prompts
from ..models.schemas import ParsedLog, LogEntry
from .gemini_client import GeminiClient


@dataclass
class FixPlan:
    """Structured fix plan"""
    
    diagnosis: str
    quick_fix: Optional[str]
    detailed_steps: List[str]
    code_changes: Dict[str, str] = field(default_factory=dict)  # file -> code
    prevention_tips: List[str] = field(default_factory=list)
    verification: str = ""
    confidence: int = 75  # 0-100
    raw_response: str = ""


class FixSuggester:
    """
    AI-powered fix suggester
    
    Generates concrete, actionable steps to fix CI/CD build errors
    with platform-specific guidance and code examples
    """
    
    def __init__(self, client: GeminiClient):
        """
        Initialize fix suggester
        
        Args:
            client: GeminiClient instance
        """
        self.client = client
    
    def suggest_fix(
        self,
        error: LogEntry,
        parsed_log: ParsedLog,
        include_code: bool = True,
    ) -> FixPlan:
        """
        Generate fix suggestion for an error
        
        Args:
            error: Error log entry
            parsed_log: Full parsed log for context
            include_code: Include code change suggestions
        
        Returns:
            Structured fix plan
        """
        # Build prompt
        prompt = self._build_prompt(error, parsed_log)
        
        # Get LLM response
        try:
            response = self.client.generate(
                prompt=prompt,
                max_tokens=1000,
                system_message=prompts.SYSTEM_MESSAGE,
            )
        except Exception as e:
            return self._fallback_fix(error, error_msg=str(e))
        
        # Parse response
        return self._parse_response(response, include_code)
    
    def suggest_fix_batch(
        self,
        errors: List[LogEntry],
        parsed_log: ParsedLog,
        max_errors: int = 3,
    ) -> List[FixPlan]:
        """
        Generate fix suggestions for multiple errors
        
        Args:
            errors: List of error entries
            parsed_log: Full parsed log
            max_errors: Maximum errors to process
        
        Returns:
            List of fix plans
        """
        fix_plans = []
        
        for error in errors[:max_errors]:
            plan = self.suggest_fix(error, parsed_log)
            fix_plans.append(plan)
        
        return fix_plans
    
    def _build_prompt(self, error: LogEntry, parsed_log: ParsedLog) -> str:
        """Build fix suggestion prompt"""
        # Create error summary (handle both enum and string level)
        level_str = error.level.value if hasattr(error.level, 'value') else str(error.level)
        error_summary = f"[{level_str}] {error.message}"
        
        # Determine environment
        environment = "Production" if "prod" in (parsed_log.job_name or "").lower() else "Development"
        
        # Find failed stage
        failed_stage = "Unknown"
        if parsed_log.stages:
            for stage in parsed_log.stages:
                status_str = stage.status.value if hasattr(stage.status, 'value') else str(stage.status)
                if status_str in ["FAILED", "ERROR"]:
                    failed_stage = stage.name
                    break
        
        # Build error details with context
        error_details = f"Error at line {error.line_number}:\n{error.message}\n\n"
        
        # Add surrounding context if available
        if parsed_log.errors:
            related_errors = [
                e for e in parsed_log.errors 
                if abs(e.line_number - error.line_number) <= 10
            ]
            if len(related_errors) > 1:
                error_details += "Related errors nearby:\n"
                for err in related_errors[:3]:
                    if err.line_number != error.line_number:
                        error_details += f"  Line {err.line_number}: {err.message[:80]}\n"
        
        # Extract stack trace if available (look for common patterns)
        stack_trace = self._extract_stack_trace(error.message)
        
        # Get platform as string
        platform_str = parsed_log.platform.value if hasattr(parsed_log.platform, 'value') else str(parsed_log.platform)
        
        # Use prompt template
        prompt = prompts.build_fix_prompt(
            error_summary=error_summary,
            platform=platform_str,
            job_name=parsed_log.job_name or "Unknown",
            environment=environment,
            failed_stage=failed_stage,
            error_details=error_details,
            stack_trace=stack_trace,
        )
        
        return prompt
    
    def _extract_stack_trace(self, message: str) -> str:
        """Extract stack trace from error message if present"""
        # Look for common stack trace patterns
        stack_patterns = [
            r'at\s+[\w.]+\([^)]+\)',  # Java/JS style
            r'File\s+"[^"]+",\s+line\s+\d+',  # Python style
            r'\w+Error:\s+.+',  # Error name
        ]
        
        stack_lines = []
        for line in message.split('\n'):
            for pattern in stack_patterns:
                if re.search(pattern, line):
                    stack_lines.append(line.strip())
                    break
        
        if stack_lines:
            return '\n'.join(stack_lines[:10])  # Max 10 lines
        return "Not available"
    
    def _parse_response(
        self,
        response: str,
        include_code: bool = True,
    ) -> FixPlan:
        """Parse LLM response into structured fix plan"""
        # Extract diagnosis (first paragraph usually)
        diagnosis = self._extract_diagnosis(response)
        
        # Extract quick fix
        quick_fix = self._extract_quick_fix(response)
        
        # Extract detailed steps
        detailed_steps = self._extract_steps(response)
        
        # Extract code changes if requested
        code_changes = {}
        if include_code:
            code_changes = self._extract_code_changes(response)
        
        # Extract prevention tips
        prevention_tips = self._extract_list(
            response, r"\*\*PREVENTION.*?\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)"
        )
        
        # Extract verification
        verification = self._extract_section(
            response, r"\*\*VERIFICATION\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)"
        )
        
        # Extract confidence
        confidence_str = self._extract_section(
            response, r"\*\*CONFIDENCE\*\*:?\s*(\d+)"
        )
        try:
            confidence = int(confidence_str) if confidence_str else 75
        except ValueError:
            confidence = 75
        
        # Fallback values
        if not diagnosis:
            diagnosis = "Unable to diagnose the issue from available information."
        
        if not detailed_steps:
            detailed_steps = ["Review the error message", "Check recent changes", "Consult documentation"]
        
        if not verification:
            verification = "Re-run the build to verify the fix."
        
        return FixPlan(
            diagnosis=diagnosis,
            quick_fix=quick_fix,
            detailed_steps=detailed_steps,
            code_changes=code_changes,
            prevention_tips=prevention_tips,
            verification=verification,
            confidence=confidence,
            raw_response=response,
        )
    
    def _extract_diagnosis(self, text: str) -> str:
        """Extract diagnosis from response"""
        # Try to find explicit diagnosis section
        match = re.search(
            r"\*\*DIAGNOSIS\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        
        # Fallback: use first paragraph before any section
        lines = text.split('\n')
        diagnosis_lines = []
        for line in lines:
            if line.strip() and not line.startswith('**'):
                diagnosis_lines.append(line.strip())
            elif diagnosis_lines and line.startswith('**'):
                break
        
        if diagnosis_lines:
            return ' '.join(diagnosis_lines)
        
        return ""
    
    def _extract_quick_fix(self, text: str) -> Optional[str]:
        """Extract quick fix command if available"""
        match = re.search(
            r"\*\*QUICK FIX\*\*.*?```(?:bash)?\s*\n(.+?)\n```",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_steps(self, text: str) -> List[str]:
        """Extract detailed steps"""
        steps = []
        
        # Find DETAILED STEPS section
        match = re.search(
            r"\*\*DETAILED STEPS\*\*:?\s*\n(.+?)(?:\n\*\*[A-Z]|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if match:
            content = match.group(1)
            # Extract numbered steps
            step_pattern = r'^\d+\.\s+(.+?)(?=\n\d+\.|\n```|\Z)'
            step_matches = re.finditer(step_pattern, content, re.MULTILINE | re.DOTALL)
            
            for step_match in step_matches:
                step_text = step_match.group(1).strip()
                # Remove code blocks from step text (they'll be separate)
                step_text = re.sub(r'```[\s\S]*?```', '[See code block]', step_text)
                steps.append(step_text)
        
        return steps
    
    def _extract_code_changes(self, text: str) -> Dict[str, str]:
        """Extract code changes with filenames"""
        code_changes = {}
        
        # Find CODE CHANGES section
        match = re.search(
            r"\*\*CODE CHANGES\*\*.*?\n(.+?)(?:\n\*\*[A-Z]|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if match:
            content = match.group(1)
            
            # Look for "File: filename" followed by code block
            file_pattern = r'File:\s*`?([^`\n]+)`?\s*\n```(?:\w+)?\s*\n(.+?)\n```'
            file_matches = re.finditer(file_pattern, content, re.DOTALL)
            
            for file_match in file_matches:
                filename = file_match.group(1).strip()
                code = file_match.group(2).strip()
                code_changes[filename] = code
        
        return code_changes
    
    def _extract_section(self, text: str, pattern: str) -> str:
        """Extract a section using regex"""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Clean up
            content = re.sub(r'\*\*[A-Z\s]+\*\*.*$', '', content, flags=re.MULTILINE)
            return content.strip()
        return ""
    
    def _extract_list(self, text: str, pattern: str) -> List[str]:
        """Extract bullet list from section"""
        items = []
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            content = match.group(1)
            lines = content.split("\n")
            
            for line in lines:
                line = line.strip()
                if line.startswith(("-", "•", "*")) or re.match(r'^\d+\.', line):
                    item = re.sub(r'^[-•*\d.]\s*', '', line).strip()
                    if item and not item.startswith("**"):
                        items.append(item)
        
        return items
    
    def _fallback_fix(
        self,
        error: LogEntry,
        error_msg: Optional[str] = None,
    ) -> FixPlan:
        """Generate basic fix suggestion without LLM"""
        return FixPlan(
            diagnosis=f"Error: {error.message[:100]}",
            quick_fix=None,
            detailed_steps=[
                "Review the error message carefully",
                "Check recent code or configuration changes",
                "Verify environment setup and dependencies",
                "Consult relevant documentation",
                "Search for similar errors online",
            ],
            code_changes={},
            prevention_tips=[
                "Add validation checks",
                "Improve error handling",
                "Add relevant tests",
            ],
            verification="Re-run the build after applying fixes",
            confidence=40,
            raw_response=f"Fallback fix (Error: {error_msg})" if error_msg else "Fallback fix",
        )
