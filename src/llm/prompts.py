"""
Prompt templates for LLM interactions
Carefully engineered prompts for optimal results
"""

# System message for all CI/CD log analysis
SYSTEM_MESSAGE = """You are an expert DevOps engineer and CI/CD specialist with deep knowledge of:
- Jenkins, GitHub Actions, GitLab CI, and other CI/CD platforms
- Common build errors and their root causes
- Best practices for fixing CI/CD issues
- Docker, Kubernetes, and cloud platforms

Your responses are:
- Concise and actionable
- Technically accurate
- Easy to understand
- Focused on solving the problem quickly
"""


# ============================================================================
# SUMMARIZATION PROMPT
# ============================================================================

SUMMARIZE_PROMPT = """Analyze this {platform} build log and provide a structured summary.

Build Information:
- Platform: {platform}
- Job Name: {job_name}
- Build Status: {status}
- Error Count: {error_count}
- Warning Count: {warning_count}
- Duration: {duration}

Log Content (first {log_size} characters):
{log_content}

Provide a summary in this exact format:

**STATUS**: [Success/Failed/Timeout/Unstable]

**MAIN ISSUE**: [One sentence describing the primary problem, or "Build completed successfully" if no issues]

**KEY POINTS**:
- [Point 1: Most critical finding]
- [Point 2: Secondary finding]
- [Point 3: Additional detail]
- [Additional points if needed, max 5 total]

**IMPACT**: [Low/Medium/High/Critical] - [Brief reason]

**CONFIDENCE**: [0-100]%

Keep it concise. Focus on actionable information.
"""


# ============================================================================
# ERROR EXPLANATION PROMPT
# ============================================================================

EXPLAIN_ERROR_PROMPT = """Analyze this CI/CD build error and provide a detailed explanation.

Error Information:
- Platform: {platform}
- Error Type: {error_type}
- Line Number: {line_number}
- Error Message:
{error_message}

Build Context:
- Job: {job_name}
- Stage: {stage_name}
- Previous Stages: {previous_stages}

Additional Context:
{additional_context}

Provide explanation in this format:

**ROOT CAUSE**:
[Clear explanation of why this error occurred]

**COMMON SCENARIOS**:
[List 2-3 common situations that lead to this error]
- Scenario 1: ...
- Scenario 2: ...
- Scenario 3: ...

**TECHNICAL DETAILS**:
[What's happening under the hood - be specific and technical]

**RELATED ERRORS**:
[If this error typically comes with other issues, mention them]

Be specific to the {platform} platform and the error context provided.
"""


# ============================================================================
# FIX SUGGESTION PROMPT
# ============================================================================

FIX_SUGGESTION_PROMPT = """You are a DevOps engineer. Provide concrete fix steps for this CI/CD build error.

Error Summary:
{error_summary}

Build Context:
- Platform: {platform}
- Job Name: {job_name}
- Build Environment: {environment}
- Stage Failed: {failed_stage}

Error Details:
{error_details}

Stack Trace (if available):
{stack_trace}

Provide fix suggestions in this format:

**QUICK FIX** (if available):
```bash
# Immediate command(s) that might fix the issue
[command]
```

**DETAILED STEPS**:
1. [First step - most important]
   ```bash
   # Command if needed
   ```
   
2. [Second step]
   ```bash
   # Command if needed
   ```

3. [Continue with 3-5 numbered steps total]

**CODE CHANGES** (if needed):
File: `path/to/file`
```language
[Show exact code change needed]
```

**PREVENTION TIPS**:
- [How to prevent this error in the future]
- [Best practice to follow]
- [Tool or check to add to CI]

**VERIFICATION**:
[How to verify the fix worked]

**CONFIDENCE**: [0-100]% - [Brief reason for confidence level]

Provide platform-specific, actionable steps. Include exact commands and code when possible.
"""


# ============================================================================
# BATCH ERROR ANALYSIS PROMPT
# ============================================================================

BATCH_ERROR_ANALYSIS_PROMPT = """Analyze multiple errors from a CI/CD build and prioritize them.

Build Information:
- Platform: {platform}
- Job: {job_name}
- Total Errors: {error_count}

Errors:
{errors_list}

Provide analysis in this format:

**PRIORITY RANKING**:
1. [Error name] - [Why this is most critical]
2. [Error name] - [Why this is second priority]
3. [Continue...]

**ROOT CAUSE ANALYSIS**:
[Are these errors related? Is there a common root cause?]

**FIX ORDER**:
[Which errors should be fixed first and why? Will fixing one resolve others?]

**RECOMMENDED ACTION**:
[Single most important action to take right now]

Focus on dependencies between errors and optimal fix order.
"""


# ============================================================================
# COMPARISON PROMPT (for comparing failed vs successful builds)
# ============================================================================

COMPARISON_PROMPT = """Compare a failed build with a successful build to identify what changed.

Failed Build:
- Build #: {failed_build_number}
- Status: {failed_status}
- Key Errors:
{failed_errors}

Successful Build (previous):
- Build #: {success_build_number}
- Status: Success
- Summary:
{success_summary}

Changes Between Builds:
{git_changes}

Provide analysis:

**WHAT CHANGED**:
[List the key differences between builds]

**LIKELY CAUSE**:
[Based on changes, what most likely caused the failure]

**ROLLBACK OPTION**:
[Can this be rolled back? How?]

**FIX APPROACH**:
[Best approach to fix based on the changes]
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_summarize_prompt(
    platform: str,
    job_name: str,
    status: str,
    error_count: int,
    warning_count: int,
    duration: str,
    log_content: str,
    log_size: int = 5000,
) -> str:
    """Build summarization prompt with provided context"""
    return SUMMARIZE_PROMPT.format(
        platform=platform,
        job_name=job_name,
        status=status,
        error_count=error_count,
        warning_count=warning_count,
        duration=duration or "Unknown",
        log_content=log_content[:log_size],
        log_size=log_size,
    )


def build_explain_prompt(
    platform: str,
    error_type: str,
    line_number: int,
    error_message: str,
    job_name: str,
    stage_name: str,
    previous_stages: str,
    additional_context: str = "",
) -> str:
    """Build error explanation prompt"""
    return EXPLAIN_ERROR_PROMPT.format(
        platform=platform,
        error_type=error_type,
        line_number=line_number,
        error_message=error_message,
        job_name=job_name,
        stage_name=stage_name,
        previous_stages=previous_stages,
        additional_context=additional_context or "None",
    )


def build_fix_prompt(
    error_summary: str,
    platform: str,
    job_name: str,
    environment: str,
    failed_stage: str,
    error_details: str,
    stack_trace: str = "",
) -> str:
    """Build fix suggestion prompt"""
    return FIX_SUGGESTION_PROMPT.format(
        error_summary=error_summary,
        platform=platform,
        job_name=job_name,
        environment=environment or "Production",
        failed_stage=failed_stage,
        error_details=error_details,
        stack_trace=stack_trace or "Not available",
    )


def build_batch_analysis_prompt(
    platform: str,
    job_name: str,
    error_count: int,
    errors_list: str,
) -> str:
    """Build batch error analysis prompt"""
    return BATCH_ERROR_ANALYSIS_PROMPT.format(
        platform=platform,
        job_name=job_name,
        error_count=error_count,
        errors_list=errors_list,
    )
