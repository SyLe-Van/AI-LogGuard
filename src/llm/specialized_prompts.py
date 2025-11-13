"""
Specialized prompts for each error category
These prompts are optimized for specific error types detected by ML
"""

# Dependency Error Prompt
DEPENDENCY_ERROR_PROMPT = """You are a CI/CD build expert specializing in dependency management.

Analyze this dependency error and provide:
1. **Root Cause**: What package/dependency is causing the issue
2. **Why It Failed**: Version conflicts, missing packages, registry issues, etc.
3. **Fix Steps**: Concrete commands to resolve (package.json, requirements.txt, pom.xml, etc.)

Platform: {platform}
Error Context:
{log_content}

Provide a clear, actionable response focused on dependency resolution."""

# Syntax Error Prompt
SYNTAX_ERROR_PROMPT = """You are a code quality expert for CI/CD builds.

Analyze this syntax/compilation error:
1. **Error Location**: Which file and line number
2. **Syntax Issue**: What's wrong with the code syntax
3. **Fix**: Show the corrected code snippet

Platform: {platform}
Error Context:
{log_content}

Focus on the exact syntax problem and provide corrected code."""

# Test Failure Prompt
TEST_FAILURE_PROMPT = """You are a testing expert analyzing CI/CD test failures.

Analyze this test failure:
1. **Failed Test**: Which test(s) failed and why
2. **Expected vs Actual**: What was expected vs what happened
3. **Root Cause**: Code logic issue, environment problem, or test issue
4. **Fix Strategy**: How to fix the failing test

Platform: {platform}
Error Context:
{log_content}

Focus on test assertions and logic issues."""

# Timeout Error Prompt
TIMEOUT_PROMPT = """You are a performance optimization expert for CI/CD.

Analyze this timeout issue:
1. **What Timed Out**: Which step/command exceeded time limit
2. **Performance Bottleneck**: What's causing the slowness
3. **Optimization Steps**: How to speed up the build
4. **Alternative Solutions**: Increase timeout vs optimize code

Platform: {platform}
Error Context:
{log_content}

Provide performance optimization suggestions."""

# Environment Error Prompt
ENVIRONMENT_ERROR_PROMPT = """You are a DevOps expert specializing in CI/CD environment configuration.

Analyze this environment/configuration error:
1. **Missing Config**: What environment variable, setting, or tool is missing
2. **Environment Mismatch**: Version differences, OS issues, etc.
3. **Configuration Fix**: How to set up the correct environment

Platform: {platform}
Error Context:
{log_content}

Focus on environment setup and configuration."""

# Network Error Prompt
NETWORK_ERROR_PROMPT = """You are a network and infrastructure expert for CI/CD.

Analyze this network/connectivity error:
1. **Connection Issue**: What endpoint/service is unreachable
2. **Network Problem**: DNS, firewall, timeout, SSL, etc.
3. **Resolution**: Retry logic, alternative endpoints, proxy config

Platform: {platform}
Error Context:
{log_content}

Focus on network connectivity and infrastructure issues."""

# Permission Error Prompt
PERMISSION_ERROR_PROMPT = """You are a security and access control expert for CI/CD.

Analyze this permission/access error:
1. **Access Denied**: What file/resource/service lacks permission
2. **Permission Issue**: File permissions, API keys, credentials, etc.
3. **Fix**: How to grant proper permissions securely

Platform: {platform}
Error Context:
{log_content}

Focus on permissions and access control."""

# General/Unknown Error Prompt (fallback)
GENERAL_ERROR_PROMPT = """You are a CI/CD troubleshooting expert.

Analyze this build error:
1. **Summary**: What went wrong in 1-2 sentences
2. **Root Cause**: The underlying issue
3. **Fix Steps**: Step-by-step resolution
4. **Prevention**: How to avoid this in future

Platform: {platform}
Error Category: {error_category}
Confidence: {confidence}

Error Context:
{log_content}

Provide a comprehensive analysis and actionable fix."""


# Prompt selector based on ML prediction
SPECIALIZED_PROMPTS = {
    'dependency_error': DEPENDENCY_ERROR_PROMPT,
    'syntax_error': SYNTAX_ERROR_PROMPT,
    'test_failure': TEST_FAILURE_PROMPT,
    'timeout': TIMEOUT_PROMPT,
    'environment_error': ENVIRONMENT_ERROR_PROMPT,
    'network_error': NETWORK_ERROR_PROMPT,
    'permission_error': PERMISSION_ERROR_PROMPT,
}


def get_specialized_prompt(error_type: str, platform: str, log_content: str, confidence: float = None) -> str:
    """
    Get specialized prompt based on ML-predicted error type
    
    Args:
        error_type: ML predicted error category
        platform: CI/CD platform (jenkins, github-actions, gitlab-ci)
        log_content: Relevant log excerpt
        confidence: ML prediction confidence
        
    Returns:
        Formatted prompt string
    """
    if error_type in SPECIALIZED_PROMPTS:
        prompt_template = SPECIALIZED_PROMPTS[error_type]
    else:
        prompt_template = GENERAL_ERROR_PROMPT
    
    return prompt_template.format(
        platform=platform,
        log_content=log_content,
        error_category=error_type,
        confidence=f"{confidence:.2%}" if confidence else "N/A"
    )
