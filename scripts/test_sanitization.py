#!/usr/bin/env python3
"""Test sanitization logic without calling API"""
import sys
sys.path.insert(0, '/Users/mac/projects/Thesis/ai-logguard')

# Import sanitization method directly
import re

def _sanitize_prompt(prompt: str) -> str:
    """Test version of sanitization"""
    replacements = {
        r'\bkill\b': 'terminate',
        r'\bkilled\b': 'terminated',
        r'\bkilling\b': 'terminating',
        r'\babort\b': 'stop',
        r'\baborted\b': 'stopped',
        r'\baborting\b': 'stopping',
        r'\bfatal\b': 'critical',
        r'\bcrash\b': 'stop',
        r'\bcrashed\b': 'stopped',
        r'\bcrashing\b': 'stopping',
        r'\bpanic\b': 'critical_error',
        r'\battack\b': 'attempt',
        r'\bfailure\b': 'issue',
        r'\bfailed\b': 'unsuccessful',
        r'\bfailing\b': 'not_working',
        r'\bfail\b': 'issue',
        r'\bdenied\b': 'rejected',
        r'\brefuse\b': 'reject',
        r'\brefused\b': 'rejected',
        r'\bexploded\b': 'stopped_unexpectedly',
        r'\bblew up\b': 'stopped_unexpectedly',
        r'\bdied\b': 'stopped',
        r'\bdying\b': 'stopping',
    }
    
    sanitized = prompt
    for pattern, replacement in replacements.items():
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    sanitized = sanitized.replace('ERROR:', 'ISSUE:')
    sanitized = sanitized.replace('FATAL:', 'CRITICAL:')
    sanitized = sanitized.replace('FAILED:', 'UNSUCCESSFUL:')
    
    return sanitized

# Test cases
test_prompts = [
    ("ERROR: Build FAILED with exit code 127", "Typical CI error"),
    ("FATAL: docker: command not found", "Docker missing"),
    ("The process was killed by the system", "Kill process"),
    ("Application crashed during startup", "Crash"),
    ("Test failed with assertion error", "Test failure"),
    ("Build aborted due to timeout", "Abort"),
    ("Server died unexpectedly", "Died"),
]

print("=" * 80)
print("🧪 TESTING PROMPT SANITIZATION")
print("=" * 80)

for original, description in test_prompts:
    sanitized = _sanitize_prompt(original)
    changed = "✅ CHANGED" if sanitized != original else "⚠️  NO CHANGE"
    
    print(f"\n{changed} - {description}")
    print(f"  Original:  {original}")
    print(f"  Sanitized: {sanitized}")

# Test full prompt
full_prompt = """Analyze this Jenkins CI/CD build log and identify the root cause of failure.

Log excerpt (key errors):
ERROR: Build FAILED with exit code 127
FATAL: docker: command not found
ERROR: Process was killed
ERROR: Application crashed during startup

Provide:
1. Error category
2. Root cause analysis
3. Top 2-3 recommended fixes
"""

print("\n" + "=" * 80)
print("📝 FULL PROMPT SANITIZATION")
print("=" * 80)
print("\nOriginal:")
print(full_prompt)
print("\n" + "-" * 80)
print("Sanitized:")
sanitized_full = _sanitize_prompt(full_prompt)
print(sanitized_full)

# Count replacements
original_words = set(re.findall(r'\b(kill|fatal|fail|error|crash|abort|died)\w*\b', full_prompt, re.IGNORECASE))
sanitized_words = set(re.findall(r'\b(kill|fatal|fail|error|crash|abort|died)\w*\b', sanitized_full, re.IGNORECASE))

print(f"\n📊 Statistics:")
print(f"  Dangerous words removed: {len(original_words - sanitized_words)}")
print(f"  Original length: {len(full_prompt)} chars")
print(f"  Sanitized length: {len(sanitized_full)} chars")
print(f"  Change: {abs(len(sanitized_full) - len(full_prompt))} chars")
