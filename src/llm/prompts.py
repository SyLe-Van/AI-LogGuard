"""
Prompt templates for AI-LogGuard LLM interactions
Well-engineered prompts for log analysis, error explanation, and fix suggestions
"""
from typing import Dict, List, Optional
from ..models.schemas import ParsedLog, LogEntry, ErrorCategory


# System prompts
SYSTEM_PROMPT_EXPERT = """You are an expert DevOps engineer and CI/CD specialist with deep knowledge of:
- Build systems (Maven, Gradle, npm, pip)
- CI/CD platforms (Jenkins, GitHub Actions, GitLab CI)
- Common build failures and their root causes
- Best practices for fixing build issues

Provide clear, actionable, and technically accurate advice."""

SYSTEM_PROMPT_CONCISE = """You are a helpful assistant that analyzes CI/CD logs.
Be concise, accurate, and provide actionable insights."""


# ============================================================================
# SUMMARIZATION PROMPTS
# ============================================================================

SUMMARIZE_LOG_PROMPT = """Analyze this CI/CD build log and provide a concise summary.

**Log Details:**
Platform: {platform}
Status: {status}
Total Lines: {total_lines}
Errors: {error_count}
Warnings: {warning_count}

**Log Content:**
{log_content}

**Instructions:**
1. Summarize what happened in 3-5 bullet points
2. Focus on key actions, failures, and outcomes
3. Highlight the most critical issues
4. Keep it under 200 words

**Summary:**"""


SUMMARIZE_LOG_WITH_STAGES_PROMPT = """Analyze this CI/CD build log with multiple stages.

**Build Information:**
- Platform: {platform}
- Status: {status}
- Stages: {stage_count}
- Errors: {error_count}, Warnings: {warning_count}

**Stages:**
{stages_info}

**Key Errors:**
{errors_summary}

**Task:**
Provide a structured summary:
1. **Overview**: What was this build trying to do?
2. **What Succeeded**: Which stages passed?
3. **What Failed**: Which stages failed and why?
4. **Impact**: How critical are the failures?

Keep it concise and actionable."""


# ============================================================================
# ERROR EXPLANATION PROMPTS
# ============================================================================

EXPLAIN_ERROR_PROMPT = """Explain this CI/CD build error in detail.

**Error Information:**
- Platform: {platform}
- Error Type: {error_type}
- Line Number: {line_number}

**Error Message:**
{error_message}

**Context:**
{context}

**Please provide:**
1. **Root Cause**: What exactly caused this error?
2. **Why It Happened**: Common scenarios that lead to this
3. **Impact**: How does this affect the build?
4. **Technical Details**: Any relevant technical information

Be specific and technical."""


EXPLAIN_DEPENDENCY_ERROR_PROMPT = """Analyze this dependency-related build error.

**Error:** {error_message}
**Platform:** {platform}
**Package Manager:** {package_manager}

**Explain:**
1. Which dependency is causing the issue?
2. Why can't it be resolved? (version conflict, not found, network issue?)
3. What dependencies might be affected?
4. Is this a transitive dependency issue?

Provide a clear technical explanation."""


EXPLAIN_TEST_FAILURE_PROMPT = """Analyze this test failure.

**Test Information:**
- Test Name: {test_name}
- Platform: {platform}
- Error: {error_message}

**Test Output:**
{test_output}

**Explain:**
1. What assertion or check failed?
2. What was expected vs what happened?
3. Is this a code bug, test bug, or environment issue?
4. How serious is this failure?

Be specific about the test failure."""


# ============================================================================
# FIX SUGGESTION PROMPTS
# ============================================================================

FIX_SUGGESTION_PROMPT = """Provide actionable steps to fix this CI/CD build error.

**Build Information:**
- Platform: {platform}
- Status: {status}
- Primary Error: {primary_error}

**Error Details:**
{error_details}

**Build Context:**
{build_context}

**Provide fix suggestions:**
1. **Immediate Fix**: Quick action to resolve this now
2. **Step-by-Step**: Detailed steps to fix
3. **Commands**: Exact commands to run (if applicable)
4. **Verification**: How to verify the fix worked
5. **Prevention**: How to prevent this in the future

Be specific, actionable, and include code/commands where relevant."""


FIX_DEPENDENCY_ERROR_PROMPT = """Suggest fixes for this dependency error.

**Error:** {error_message}
**Platform:** {platform}
**Package Manager:** {package_manager}

**Provide:**
1. **Quick Fix**: Immediate command to try
2. **Root Cause Fix**: Proper solution to resolve underlying issue
3. **Commands**: Exact commands with flags
4. **Verification**: How to check if resolved
5. **Alternative Solutions**: Other approaches if primary doesn't work

Example format for npm:
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

Be specific to the package manager and platform."""


FIX_TEST_FAILURE_PROMPT = """Suggest fixes for this test failure.

**Test:** {test_name}
**Error:** {error_message}
**Platform:** {platform}

**Provide:**
1. **Code Fix**: If it's a code issue, suggest the fix
2. **Test Fix**: If it's a test issue, suggest changes
3. **Environment Fix**: If it's environment-related
4. **Debugging Steps**: How to investigate further
5. **Quick Workaround**: Temporary fix if needed

Include code snippets where helpful."""


CONTEXT_AWARE_FIX_PROMPT = """Based on the error category, provide targeted fix suggestions.

**Error Category:** {error_category}
**Error:** {error_message}
**Platform:** {platform}

**Context:**
{additional_context}

**Provide category-specific fixes:**
- For DEPENDENCY_ERROR: Focus on package management
- For SYNTAX_ERROR: Focus on code fixes
- For TEST_FAILURE: Focus on test debugging
- For TIMEOUT: Focus on performance/resources
- For ENVIRONMENT_ERROR: Focus on configuration

Give 3-5 concrete, actionable steps."""


# ============================================================================
# MULTI-ERROR ANALYSIS
# ============================================================================

ANALYZE_MULTIPLE_ERRORS_PROMPT = """Analyze multiple errors in this build and identify relationships.

**Build Status:** {status}
**Platform:** {platform}
**Errors Found:** {error_count}

**Errors:**
{errors_list}

**Tasks:**
1. **Primary Error**: Which error happened first/is most critical?
2. **Cascading Effects**: Which errors are consequences of others?
3. **Independent Issues**: Which errors are unrelated?
4. **Fix Order**: What order should these be fixed in?

Provide a clear analysis and prioritization."""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_log_for_prompt(parsed_log: ParsedLog, max_lines: int = 100) -> str:
    """
    Format parsed log for inclusion in prompt
    
    Args:
        parsed_log: Parsed log object
        max_lines: Maximum lines to include
        
    Returns:
        Formatted log string
    """
    lines = parsed_log.raw_content.splitlines()
    
    if len(lines) <= max_lines:
        return parsed_log.raw_content
    
    # Include beginning and end with ellipsis in middle
    start = lines[:max_lines // 2]
    end = lines[-(max_lines // 2):]
    
    return (
        "\n".join(start) +
        f"\n\n... ({len(lines) - max_lines} lines omitted) ...\n\n" +
        "\n".join(end)
    )


def format_stages_info(parsed_log: ParsedLog) -> str:
    """Format stages information for prompt"""
    if not parsed_log.stages:
        return "No stages information available"
    
    lines = []
    for i, stage in enumerate(parsed_log.stages, 1):
        status_icon = "✅" if stage.status == "SUCCESS" else "❌"
        lines.append(
            f"{i}. {status_icon} {stage.name} - {stage.status} "
            f"(Errors: {stage.error_count}, Warnings: {stage.warning_count})"
        )
    
    return "\n".join(lines)


def format_errors_summary(parsed_log: ParsedLog, max_errors: int = 5) -> str:
    """Format top errors for prompt"""
    if not parsed_log.errors:
        return "No errors found"
    
    lines = []
    for i, error in enumerate(parsed_log.errors[:max_errors], 1):
        lines.append(f"{i}. Line {error.line_number}: {error.message}")
    
    if len(parsed_log.errors) > max_errors:
        lines.append(f"... and {len(parsed_log.errors) - max_errors} more errors")
    
    return "\n".join(lines)


def select_prompt_for_error_category(category: ErrorCategory) -> str:
    """
    Select appropriate prompt template based on error category
    
    Args:
        category: Error category
        
    Returns:
        Prompt template string
    """
    prompt_map = {
        ErrorCategory.DEPENDENCY_ERROR: FIX_DEPENDENCY_ERROR_PROMPT,
        ErrorCategory.TEST_FAILURE: FIX_TEST_FAILURE_PROMPT,
        ErrorCategory.SYNTAX_ERROR: FIX_SUGGESTION_PROMPT,
        ErrorCategory.TIMEOUT: FIX_SUGGESTION_PROMPT,
        ErrorCategory.ENVIRONMENT_ERROR: FIX_SUGGESTION_PROMPT,
    }
    
    return prompt_map.get(category, FIX_SUGGESTION_PROMPT)
