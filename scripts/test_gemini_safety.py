#!/usr/bin/env python3
"""Test Gemini safety settings with error logs"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.llm.gemini_client import GeminiClient

# Test prompt with ERROR keywords
test_prompt = """Analyze this Jenkins CI/CD build log and identify the root cause of failure.

Log excerpt:
[2025-11-12T16:44:40.085Z] node: error while loading shared libraries: libatomic.so.1: cannot open shared object file: No such file or directory
ERROR: Stage "🔍 Code Quality" skipped due to earlier failure(s)
ERROR: Stage "Lint" skipped due to earlier failure(s)
ERROR: Stage "Type Check" skipped due to earlier failure(s)
FAILED in branch Lint
FAILED in branch Type Check

Provide:
1. Error category
2. Root cause analysis
3. Recommended fixes
"""

print("Testing Gemini with ERROR-heavy log content...")
print("=" * 70)

try:
    client = GeminiClient()
    print(f"✅ Client created: {client.model_name}")
    print(f"🔒 Safety settings: {len(client.safety_settings)} categories set to BLOCK_NONE")
    
    print("\n📝 Sending prompt with ERROR keywords...")
    response = client.generate(test_prompt, max_tokens=500, temperature=0.3)
    
    print("\n✅ Response received successfully!")
    print("=" * 70)
    print(response)
    print("=" * 70)
    
    tokens = client.count_tokens(response)
    print(f"\n📊 Response tokens: {tokens}")
    print("\n✅ Safety settings working correctly!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
