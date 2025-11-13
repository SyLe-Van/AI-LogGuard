#!/usr/bin/env python3
"""
Test Gemini API directly to diagnose connection issues
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.gemini_client import GeminiClient

def test_simple_api_call():
    """Test with simplest possible prompt"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not set!")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    try:
        print("🧪 Test 1: Initialize client")
        client = GeminiClient(api_key=api_key)
        print("   ✅ Client initialized")
        print()
        
        print("🧪 Test 2: Simple 'Hello' prompt (max 50 tokens)")
        print("   ⏳ Calling API...")
        
        response = client.generate(
            prompt="Say hello in one sentence.",
            max_tokens=50,
            temperature=0.1
        )
        
        print(f"   ✅ Response received: {response[:100]}")
        print()
        print("=" * 70)
        print("🎉 Gemini API is working!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing Gemini API Connection")
    print("=" * 70 + "\n")
    
    success = test_simple_api_call()
    
    if not success:
        print("\n⚠️  Possible issues:")
        print("  1. API key not activated yet (wait 1-2 minutes)")
        print("  2. Network/firewall blocking Google AI")
        print("  3. API quota exceeded")
        print("  4. Wrong API key")
        print("\n💡 Try:")
        print("  - Wait a minute and retry")
        print("  - Check https://aistudio.google.com/app/apikey")
        print("  - Test from browser: https://aistudio.google.com/")
    print()
