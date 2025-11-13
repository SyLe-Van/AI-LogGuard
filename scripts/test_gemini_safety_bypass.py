#!/usr/bin/env python3
"""Test Gemini safety filter bypass"""
import sys
import os

# Add src to path
sys.path.insert(0, '/Users/mac/projects/Thesis/ai-logguard')

# Direct import to avoid circular dependencies
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Set API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not set!")
    sys.exit(1)

# Test log với nhiều "ERROR", "FAILED", "FATAL" - thường trigger safety
test_log = """
[ERROR] Build FAILED with exit code 127
[FATAL] docker: command not found
[ERROR] /var/jenkins_home/workspace/script.sh: line 1: docker: not found
[FAILED] npm ERR! code ELIFECYCLE
[ERROR] Process terminated with exit status 1
[FATAL] Application crashed during startup
[ERROR] Connection refused - cannot connect to database
"""

# Test prompt (như trong hybrid analyzer)
prompt = f"""Analyze this Jenkins CI/CD build log and identify the root cause of issues.

Log excerpt (key errors):
{test_log}

Provide:
1. Error category
2. Root cause analysis  
3. Top 2-3 recommended fixes (concise)
"""

print("=" * 80)
print("🧪 TESTING GEMINI SAFETY FILTER BYPASS")
print("=" * 80)

print("\n📋 Test Log:")
print(test_log)

print("\n🔧 Strategy:")
print("1. Sanitize prompt (replace FATAL→CRITICAL, FAILED→UNSUCCESSFUL, etc.)")
print("2. Use Flash model with BLOCK_NONE safety settings")
print("3. If blocked, retry with Gemini Pro model")

# Configure Gemini
genai.configure(api_key=api_key)

# Safety settings - BLOCK_NONE for all categories
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# Initialize client
try:
    # Try with Flash first
    print("\n⏳ Trying with Gemini 2.0 Flash model...")
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 500,
        },
        safety_settings=safety_settings,
    )
    
    print("\n⏳ Generating response with safety bypass...")
    print("-" * 80)
    
    response = model.generate_content(prompt)
    
    # Check if blocked
    if not response.candidates or response.candidates[0].finish_reason == 2:
        print("\n⚠️  Flash model blocked! Trying with Pro model...")
        
        # Try with Pro model
        model_pro = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 500,
            },
            safety_settings=safety_settings,
        )
        
        response = model_pro.generate_content(prompt)
        
        if not response.candidates or response.candidates[0].finish_reason == 2:
            raise ValueError("Both Flash and Pro models blocked by safety filters")
    
    print("\n✅ SUCCESS! Response generated:")
    print("-" * 80)
    print(response.text)
    print("-" * 80)
    
    print(f"\n📊 Response length: {len(response.text)} chars")
    print(f"📊 Tokens used: ~{len(response.text) // 4}")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    print("\n💡 This means all safety bypass attempts failed.")
    print("   The log content may be too 'dangerous' for Gemini's filters.")
