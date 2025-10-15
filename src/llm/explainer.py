"""
LLM-powered error explainer
Provides detailed explanations of CI/CD build errors
"""
from typing import Dict, List, Optional
import logging
from ..models.schemas import ParsedLog, LogEntry, ErrorCategory
from .openai_client import get_openai_client
from .prompts import (
    SYSTEM_PROMPT_EXPERT,
    EXPLAIN_ERROR_PROMPT,
    EXPLAIN_DEPENDENCY_ERROR_PROMPT,
    EXPLAIN_TEST_FAILURE_PROMPT,
    select_prompt_for_error_category
)


logger = logging.getLogger(__name__)


class ErrorExplainer:
    """
    Provides detailed explanations of build errors using LLM
    
    Features:
    - Context-aware error analysis
    - Category-specific explanations (dependency, test, syntax, etc.)
    - Multi-error relationship analysis
    - Root cause identification
    """
    
    def __init__(self, 
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.2,
                 max_tokens: int = 600):
        """
        Initialize error explainer
        
        Args:
            model: OpenAI model to use
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.client = get_openai_client()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def explain_error(self, 
                     error: LogEntry,
                     parsed_log: ParsedLog,
                     context_lines: int = 5) -> Dict[str, any]:
        """
        Explain a specific error in detail
        
        Args:
            error: Error entry to explain
            parsed_log: Full parsed log for context
            context_lines: Lines of context before/after error
            
        Returns:
            Dictionary with explanation, category, tokens used
        """
        # Detect error category if not already set
        error_category = error.category or self._detect_category(error.message)
        
        # Build context from surrounding lines
        context = self._extract_context(
            parsed_log.raw_content,
            error.line_number,
            context_lines
        )
        
        # Select appropriate prompt
        prompt = self._build_explanation_prompt(
            error=error,
            error_category=error_category,
            context=context,
            platform=parsed_log.platform.value
        )
        
        # Call LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_EXPERT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat_completion(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return {
            "explanation": response["content"],
            "error_category": error_category.value if error_category else "UNKNOWN",
            "line_number": error.line_number,
            "tokens_used": response["tokens"],
            "model": response["model"]
        }
    
    def explain_top_errors(self, 
                          parsed_log: ParsedLog,
                          max_errors: int = 3) -> List[Dict[str, any]]:
        """
        Explain the top N most critical errors
        
        Args:
            parsed_log: Parsed log with errors
            max_errors: Maximum number of errors to explain
            
        Returns:
            List of error explanations
        """
        if not parsed_log.errors:
            return []
        
        # Take first N errors (usually most critical)
        top_errors = parsed_log.errors[:max_errors]
        
        explanations = []
        for i, error in enumerate(top_errors, 1):
            logger.info(f"Explaining error {i}/{len(top_errors)}: Line {error.line_number}")
            
            explanation = self.explain_error(error, parsed_log)
            explanation["error_index"] = i
            explanation["error_message"] = error.message
            
            explanations.append(explanation)
        
        return explanations
    
    def analyze_error_relationships(self, 
                                   parsed_log: ParsedLog) -> Dict[str, any]:
        """
        Analyze relationships between multiple errors
        
        Identifies:
        - Primary/root cause errors
        - Cascading failures
        - Independent issues
        - Fix prioritization
        
        Args:
            parsed_log: Parsed log with multiple errors
            
        Returns:
            Dictionary with relationship analysis
        """
        if len(parsed_log.errors) <= 1:
            return {"has_multiple_errors": False}
        
        # Build prompt with all errors
        errors_list = "\n".join([
            f"{i+1}. Line {err.line_number}: {err.message}"
            for i, err in enumerate(parsed_log.errors[:10])  # Limit to first 10
        ])
        
        prompt = f"""Analyze these build errors and identify their relationships:

**Build Status:** {parsed_log.status.value}
**Platform:** {parsed_log.platform.value}
**Total Errors:** {len(parsed_log.errors)}

**Errors:**
{errors_list}

**Analyze:**
1. **Primary Error**: Which error is the root cause?
2. **Cascading Effects**: Which errors are consequences of the primary error?
3. **Independent Issues**: Which errors are unrelated?
4. **Fix Priority**: What order should these be fixed in?

Provide a clear analysis."""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_EXPERT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat_completion(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=800
        )
        
        return {
            "has_multiple_errors": True,
            "error_count": len(parsed_log.errors),
            "analysis": response["content"],
            "tokens_used": response["tokens"],
            "model": response["model"]
        }
    
    def _detect_category(self, error_message: str) -> Optional[ErrorCategory]:
        """Detect error category from message content"""
        error_lower = error_message.lower()
        
        # Dependency errors
        if any(keyword in error_lower for keyword in [
            "could not find", "not found", "dependency", "package",
            "module not found", "cannot resolve", "npm err"
        ]):
            return ErrorCategory.DEPENDENCY_ERROR
        
        # Syntax errors
        if any(keyword in error_lower for keyword in [
            "syntax error", "unexpected token", "parse error",
            "invalid syntax", "compilation failed"
        ]):
            return ErrorCategory.SYNTAX_ERROR
        
        # Test failures
        if any(keyword in error_lower for keyword in [
            "test failed", "assertion", "expected", "actual",
            "junit", "spec failed"
        ]):
            return ErrorCategory.TEST_FAILURE
        
        # Timeout errors
        if any(keyword in error_lower for keyword in [
            "timeout", "timed out", "time limit exceeded"
        ]):
            return ErrorCategory.TIMEOUT
        
        # Environment errors
        if any(keyword in error_lower for keyword in [
            "permission denied", "access denied", "command not found",
            "no such file", "connection refused"
        ]):
            return ErrorCategory.ENVIRONMENT_ERROR
        
        return None
    
    def _extract_context(self, 
                        raw_content: str, 
                        line_number: int,
                        context_lines: int) -> str:
        """Extract context lines around an error"""
        lines = raw_content.splitlines()
        
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context_with_markers = []
        for i in range(start, end):
            marker = ">>> " if i == line_number - 1 else "    "
            context_with_markers.append(f"{marker}{lines[i]}")
        
        return "\n".join(context_with_markers)
    
    def _build_explanation_prompt(self,
                                 error: LogEntry,
                                 error_category: Optional[ErrorCategory],
                                 context: str,
                                 platform: str) -> str:
        """Build appropriate prompt based on error category"""
        
        # Use category-specific prompt if available
        if error_category == ErrorCategory.DEPENDENCY_ERROR:
            # Try to detect package manager
            package_manager = self._detect_package_manager(context)
            return EXPLAIN_DEPENDENCY_ERROR_PROMPT.format(
                error_message=error.message,
                platform=platform,
                package_manager=package_manager
            )
        
        elif error_category == ErrorCategory.TEST_FAILURE:
            # Extract test name if possible
            test_name = self._extract_test_name(error.message)
            return EXPLAIN_TEST_FAILURE_PROMPT.format(
                test_name=test_name,
                platform=platform,
                error_message=error.message,
                test_output=context
            )
        
        else:
            # Generic error explanation
            error_type = error_category.value if error_category else "Unknown"
            return EXPLAIN_ERROR_PROMPT.format(
                platform=platform,
                error_type=error_type,
                line_number=error.line_number,
                error_message=error.message,
                context=context
            )
    
    def _detect_package_manager(self, context: str) -> str:
        """Detect package manager from context"""
        context_lower = context.lower()
        
        if "npm" in context_lower or "package.json" in context_lower:
            return "npm"
        elif "pip" in context_lower or "requirements.txt" in context_lower:
            return "pip"
        elif "maven" in context_lower or "pom.xml" in context_lower:
            return "maven"
        elif "gradle" in context_lower or "build.gradle" in context_lower:
            return "gradle"
        else:
            return "unknown"
    
    def _extract_test_name(self, error_message: str) -> str:
        """Extract test name from error message"""
        # Simple extraction - can be improved with regex
        if "test" in error_message.lower():
            parts = error_message.split()
            for i, part in enumerate(parts):
                if "test" in part.lower() and i + 1 < len(parts):
                    return parts[i + 1].strip(":,.")
        
        return "Unknown test"


# Convenience function
def explain_error(error: LogEntry,
                 parsed_log: ParsedLog,
                 model: str = "gpt-3.5-turbo") -> Dict[str, any]:
    """
    Explain a single error
    
    Args:
        error: Error to explain
        parsed_log: Full log for context
        model: OpenAI model to use
        
    Returns:
        Explanation dictionary
    """
    explainer = ErrorExplainer(model=model)
    return explainer.explain_error(error, parsed_log)
