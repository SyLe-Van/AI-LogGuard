"""
Error Explainer using LLM
Provides detailed explanations for CI/CD build errors
"""
import re
from dataclasses import dataclass
from typing import List, Optional

from . import prompts
from ..models.schemas import ParsedLog, LogEntry
from .gemini_client import GeminiClient


@dataclass
class ErrorExplanation:
    """Structured error explanation"""
    
    error_message: str
    root_cause: str
    common_scenarios: List[str]
    technical_details: str
    related_errors: List[str]
    confidence: int  # 0-100
    raw_response: str


class ErrorExplainer:
    """
    AI-powered error explainer
    
    Provides detailed, context-aware explanations
    for CI/CD build errors
    """
    
    def __init__(self, client: GeminiClient):
        """
        Initialize explainer
        
        Args:
            client: GeminiClient instance
        """
        self.client = client
    
    def explain(
        self,
        error: LogEntry,
        parsed_log: ParsedLog,
    ) -> ErrorExplanation:
        """
        Explain a single error with context
        
        Args:
            error: Error log entry
            parsed_log: Full parsed log for context
        
        Returns:
            Detailed error explanation
        """
        # Build prompt with error context
        prompt = self._build_prompt(error, parsed_log)
        
        # Get LLM response
        try:
            response = self.client.generate(
                prompt=prompt,
                max_tokens=800,
                system_message=prompts.SYSTEM_MESSAGE,
            )
        except Exception as e:
            return self._fallback_explanation(error, error_msg=str(e))
        
        # Parse response
        return self._parse_response(response, error)
    
    def explain_batch(
        self,
        errors: List[LogEntry],
        parsed_log: ParsedLog,
        max_errors: int = 5,
    ) -> List[ErrorExplanation]:
        """
        Explain multiple errors (batch processing)
        
        Args:
            errors: List of error entries
            parsed_log: Full parsed log
            max_errors: Maximum number of errors to explain
        
        Returns:
            List of error explanations
        """
        explanations = []
        
        # Limit to max_errors
        errors_to_explain = errors[:max_errors]
        
        for error in errors_to_explain:
            explanation = self.explain(error, parsed_log)
            explanations.append(explanation)
        
        return explanations
    
    def _build_prompt(self, error: LogEntry, parsed_log: ParsedLog) -> str:
        """Build explanation prompt with context"""
        # Determine error type from message
        error_type = self._classify_error(error.message)
        
        # Get stage context
        stage_name = "Unknown"
        previous_stages = "None"
        
        if parsed_log.stages:
            # Find which stage this error belongs to
            for stage in parsed_log.stages:
                if stage.error_count > 0:
                    stage_name = stage.name
                    break
            
            # Get previous successful stages (handle both enum and string status)
            prev_stages = []
            for s in parsed_log.stages:
                status = s.status.value if hasattr(s.status, 'value') else str(s.status)
                if status == "SUCCESS":
                    prev_stages.append(s.name)
            if prev_stages:
                previous_stages = ", ".join(prev_stages[:5])
        
        # Build additional context
        additional_context = f"Total errors: {parsed_log.error_count}\n"
        if parsed_log.triggered_by:
            additional_context += f"Triggered by: {parsed_log.triggered_by}\n"
        
        # Get platform as string
        platform_str = parsed_log.platform.value if hasattr(parsed_log.platform, 'value') else str(parsed_log.platform)
        
        # Use prompt template
        prompt = prompts.build_explain_prompt(
            platform=platform_str,
            error_type=error_type,
            line_number=error.line_number,
            error_message=error.message,
            job_name=parsed_log.job_name or "Unknown",
            stage_name=stage_name,
            previous_stages=previous_stages,
            additional_context=additional_context,
        )
        
        return prompt
    
    def _classify_error(self, message: str) -> str:
        """Classify error type from message"""
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in ["dependency", "package", "npm", "pip", "not found"]):
            return "Dependency Error"
        elif any(kw in message_lower for kw in ["syntax", "parse", "unexpected token"]):
            return "Syntax Error"
        elif any(kw in message_lower for kw in ["test failed", "assertion", "expect"]):
            return "Test Failure"
        elif any(kw in message_lower for kw in ["timeout", "timed out"]):
            return "Timeout"
        elif any(kw in message_lower for kw in ["permission", "denied", "forbidden"]):
            return "Permission Error"
        elif any(kw in message_lower for kw in ["docker", "container", "image"]):
            return "Docker/Container Error"
        elif any(kw in message_lower for kw in ["network", "connection", "refused"]):
            return "Network Error"
        else:
            return "General Error"
    
    def _parse_response(
        self,
        response: str,
        error: LogEntry,
    ) -> ErrorExplanation:
        """Parse LLM response into structured explanation"""
        # Extract sections
        root_cause = self._extract_section(
            response, r"\*\*ROOT CAUSE\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)"
        )
        technical_details = self._extract_section(
            response, r"\*\*TECHNICAL DETAILS\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)"
        )
        
        # Extract common scenarios (list)
        common_scenarios = self._extract_list(
            response, r"\*\*COMMON SCENARIOS\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)"
        )
        
        # Extract related errors
        related_errors = self._extract_list(
            response, r"\*\*RELATED ERRORS\*\*:?\s*\n(.+?)(?:\n\*\*|\Z)"
        )
        
        # Extract confidence if available
        confidence_str = self._extract_section(
            response, r"\*\*CONFIDENCE\*\*:?\s*(\d+)"
        )
        try:
            confidence = int(confidence_str) if confidence_str else 80
        except ValueError:
            confidence = 80
        
        # Fallback values
        if not root_cause:
            root_cause = "Unable to determine root cause from log context."
        
        if not technical_details:
            technical_details = "See error message for details."
        
        if not common_scenarios:
            common_scenarios = ["Check error message", "Review recent code changes"]
        
        return ErrorExplanation(
            error_message=error.message,
            root_cause=root_cause.strip(),
            common_scenarios=common_scenarios,
            technical_details=technical_details.strip(),
            related_errors=related_errors,
            confidence=confidence,
            raw_response=response,
        )
    
    def _extract_section(self, text: str, pattern: str) -> str:
        """Extract a section using regex"""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Remove any trailing section markers
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
                # Check if it's a list item
                if line.startswith(("-", "•", "*")) or re.match(r'^\d+\.', line):
                    # Remove bullet/number and clean
                    item = re.sub(r'^[-•*\d.]\s*', '', line).strip()
                    if item and not item.startswith("**"):  # Not a section header
                        items.append(item)
                # Also handle lines like "Scenario 1: ..."
                elif re.match(r'^(Scenario|Case|Example)\s+\d+:', line, re.IGNORECASE):
                    items.append(line)
        
        return items
    
    def _fallback_explanation(
        self,
        error: LogEntry,
        error_msg: Optional[str] = None,
    ) -> ErrorExplanation:
        """Generate basic explanation without LLM"""
        error_type = self._classify_error(error.message)
        
        return ErrorExplanation(
            error_message=error.message,
            root_cause=f"This appears to be a {error_type}. Review the error message for details.",
            common_scenarios=[
                "Check recent code/config changes",
                "Verify environment setup",
                "Review build logs for context",
            ],
            technical_details="LLM explanation unavailable. Check error message and context.",
            related_errors=[],
            confidence=40,
            raw_response=f"Fallback explanation (Error: {error_msg})" if error_msg else "Fallback explanation",
        )
