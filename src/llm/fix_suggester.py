"""
LLM-powered fix suggester
Provides actionable fix recommendations for CI/CD build errors
"""
from typing import Dict, List, Optional
import logging
from ..models.schemas import ParsedLog, LogEntry, ErrorCategory, Platform
from .openai_client import get_openai_client
from .prompts import (
    SYSTEM_PROMPT_EXPERT,
    FIX_SUGGESTION_PROMPT,
    FIX_DEPENDENCY_ERROR_PROMPT,
    FIX_TEST_FAILURE_PROMPT,
    CONTEXT_AWARE_FIX_PROMPT
)


logger = logging.getLogger(__name__)


class FixSuggester:
    """
    Generates actionable fix suggestions for build errors using LLM
    
    Features:
    - Category-specific fix recommendations
    - Step-by-step fix instructions
    - Executable commands
    - Verification steps
    - Prevention advice
    """
    
    def __init__(self, 
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.3,
                 max_tokens: int = 800):
        """
        Initialize fix suggester
        
        Args:
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.client = get_openai_client()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def suggest_fix(self,
                   error: LogEntry,
                   parsed_log: ParsedLog,
                   context_lines: int = 10) -> Dict[str, any]:
        """
        Generate fix suggestions for a specific error
        
        Args:
            error: Error to fix
            parsed_log: Full parsed log for context
            context_lines: Lines of context around error
            
        Returns:
            Dictionary with fix suggestions, commands, and verification steps
        """
        # Detect error category
        error_category = error.category or self._detect_category(error.message)
        
        # Extract context
        context = self._extract_context(
            parsed_log.raw_content,
            error.line_number,
            context_lines
        )
        
        # Build appropriate prompt
        prompt = self._build_fix_prompt(
            error=error,
            error_category=error_category,
            context=context,
            parsed_log=parsed_log
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
            "fix_suggestions": response["content"],
            "error_category": error_category.value if error_category else "UNKNOWN",
            "error_message": error.message,
            "line_number": error.line_number,
            "tokens_used": response["tokens"],
            "model": response["model"]
        }
    
    def suggest_fixes_for_top_errors(self,
                                    parsed_log: ParsedLog,
                                    max_errors: int = 3) -> List[Dict[str, any]]:
        """
        Generate fix suggestions for top N errors
        
        Args:
            parsed_log: Parsed log with errors
            max_errors: Maximum number of errors to provide fixes for
            
        Returns:
            List of fix suggestion dictionaries
        """
        if not parsed_log.errors:
            return []
        
        top_errors = parsed_log.errors[:max_errors]
        
        fix_suggestions = []
        for i, error in enumerate(top_errors, 1):
            logger.info(f"Generating fix for error {i}/{len(top_errors)}: Line {error.line_number}")
            
            suggestion = self.suggest_fix(error, parsed_log)
            suggestion["priority"] = i
            
            fix_suggestions.append(suggestion)
        
        return fix_suggestions
    
    def suggest_comprehensive_fix(self, parsed_log: ParsedLog) -> Dict[str, any]:
        """
        Generate a comprehensive fix plan for the entire build
        
        Considers:
        - All errors
        - Build status
        - Platform-specific issues
        - Fix order/priority
        
        Args:
            parsed_log: Parsed log
            
        Returns:
            Comprehensive fix plan
        """
        # Gather build information
        primary_error = parsed_log.errors[0] if parsed_log.errors else None
        
        if not primary_error:
            return {
                "has_errors": False,
                "message": "No errors detected in build"
            }
        
        # Build comprehensive context
        error_summary = "\n".join([
            f"- Line {err.line_number}: {err.message}"
            for err in parsed_log.errors[:5]  # Top 5 errors
        ])
        
        build_context = self._build_context_summary(parsed_log)
        
        prompt = FIX_SUGGESTION_PROMPT.format(
            platform=parsed_log.platform.value,
            status=parsed_log.status.value,
            primary_error=primary_error.message,
            error_details=error_summary,
            build_context=build_context
        )
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_EXPERT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat_completion(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=1000  # More tokens for comprehensive plan
        )
        
        return {
            "has_errors": True,
            "error_count": len(parsed_log.errors),
            "fix_plan": response["content"],
            "tokens_used": response["tokens"],
            "model": response["model"]
        }
    
    def generate_fix_commands(self,
                            error: LogEntry,
                            parsed_log: ParsedLog) -> List[str]:
        """
        Extract executable commands from fix suggestions
        
        Args:
            error: Error to fix
            parsed_log: Full parsed log
            
        Returns:
            List of executable commands
        """
        suggestion = self.suggest_fix(error, parsed_log)
        
        # Extract commands from markdown code blocks
        commands = []
        lines = suggestion["fix_suggestions"].split("\n")
        
        in_code_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            
            if in_code_block and line.strip():
                # Skip comments
                if not line.strip().startswith("#"):
                    commands.append(line.strip())
        
        return commands
    
    def _detect_category(self, error_message: str) -> Optional[ErrorCategory]:
        """Detect error category from message"""
        error_lower = error_message.lower()
        
        if any(k in error_lower for k in ["dependency", "not found", "cannot resolve"]):
            return ErrorCategory.DEPENDENCY_ERROR
        elif any(k in error_lower for k in ["syntax", "parse error", "unexpected"]):
            return ErrorCategory.SYNTAX_ERROR
        elif any(k in error_lower for k in ["test", "assertion", "expected"]):
            return ErrorCategory.TEST_FAILURE
        elif any(k in error_lower for k in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT
        elif any(k in error_lower for k in ["permission", "access", "not found"]):
            return ErrorCategory.ENVIRONMENT_ERROR
        
        return None
    
    def _extract_context(self, raw_content: str, line_number: int, context_lines: int) -> str:
        """Extract context around error line"""
        lines = raw_content.splitlines()
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context = []
        for i in range(start, end):
            marker = ">>> ERROR >>> " if i == line_number - 1 else ""
            context.append(f"{marker}{lines[i]}")
        
        return "\n".join(context)
    
    def _build_fix_prompt(self,
                         error: LogEntry,
                         error_category: Optional[ErrorCategory],
                         context: str,
                         parsed_log: ParsedLog) -> str:
        """Build appropriate fix prompt based on error category"""
        
        platform = parsed_log.platform.value
        
        # Category-specific prompts
        if error_category == ErrorCategory.DEPENDENCY_ERROR:
            package_manager = self._detect_package_manager(context, parsed_log.platform)
            return FIX_DEPENDENCY_ERROR_PROMPT.format(
                error_message=error.message,
                platform=platform,
                package_manager=package_manager
            )
        
        elif error_category == ErrorCategory.TEST_FAILURE:
            test_name = self._extract_test_name(error.message)
            return FIX_TEST_FAILURE_PROMPT.format(
                test_name=test_name,
                error_message=error.message,
                platform=platform
            )
        
        else:
            # Context-aware generic fix
            additional_context = self._build_error_context(error, context)
            return CONTEXT_AWARE_FIX_PROMPT.format(
                error_category=error_category.value if error_category else "UNKNOWN",
                error_message=error.message,
                platform=platform,
                additional_context=additional_context
            )
    
    def _build_context_summary(self, parsed_log: ParsedLog) -> str:
        """Build context summary for comprehensive fix"""
        parts = [
            f"Total lines: {parsed_log.total_lines}",
            f"Errors: {len(parsed_log.errors)}",
            f"Warnings: {len(parsed_log.warnings)}"
        ]
        
        if parsed_log.stages:
            failed_stages = [s for s in parsed_log.stages if s.status == "FAILURE"]
            if failed_stages:
                stage_names = ", ".join(s.name for s in failed_stages)
                parts.append(f"Failed stages: {stage_names}")
        
        if parsed_log.build_duration:
            parts.append(f"Build duration: {parsed_log.build_duration}s")
        
        return " | ".join(parts)
    
    def _build_error_context(self, error: LogEntry, context: str) -> str:
        """Build additional context for error"""
        parts = [f"Error at line {error.line_number}"]
        
        if error.category:
            parts.append(f"Category: {error.category.value}")
        
        # Add context snippet
        parts.append(f"\nContext:\n{context}")
        
        return "\n".join(parts)
    
    def _detect_package_manager(self, context: str, platform: Platform) -> str:
        """Detect package manager from context and platform"""
        context_lower = context.lower()
        
        # Platform hints
        if platform == Platform.JENKINS:
            if "mvn" in context_lower or "pom.xml" in context_lower:
                return "maven"
            elif "gradle" in context_lower:
                return "gradle"
        
        # Generic detection
        if "npm" in context_lower or "package.json" in context_lower:
            return "npm"
        elif "pip" in context_lower or "requirements.txt" in context_lower:
            return "pip"
        elif "maven" in context_lower:
            return "maven"
        elif "gradle" in context_lower:
            return "gradle"
        
        return "unknown"
    
    def _extract_test_name(self, error_message: str) -> str:
        """Extract test name from error message"""
        # Look for common test name patterns
        if "test_" in error_message.lower():
            parts = error_message.split()
            for part in parts:
                if part.startswith("test_"):
                    return part.strip(":,.()")
        
        return "Unknown test"


# Convenience functions
def suggest_fix(error: LogEntry,
               parsed_log: ParsedLog,
               model: str = "gpt-3.5-turbo") -> Dict[str, any]:
    """
    Generate fix suggestion for a single error
    
    Args:
        error: Error to fix
        parsed_log: Full log
        model: OpenAI model
        
    Returns:
        Fix suggestion dictionary
    """
    suggester = FixSuggester(model=model)
    return suggester.suggest_fix(error, parsed_log)


def suggest_comprehensive_fix(parsed_log: ParsedLog,
                             model: str = "gpt-3.5-turbo") -> Dict[str, any]:
    """
    Generate comprehensive fix plan
    
    Args:
        parsed_log: Parsed log
        model: OpenAI model
        
    Returns:
        Comprehensive fix plan
    """
    suggester = FixSuggester(model=model)
    return suggester.suggest_comprehensive_fix(parsed_log)
