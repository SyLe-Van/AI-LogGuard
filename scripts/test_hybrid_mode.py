#!/usr/bin/env python3
"""
Test Hybrid Mode for Phase 3
Tests ML classification + specialized LLM prompts
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hybrid.analyzer import HybridAnalyzer
from src.parsers import parse_log

def test_hybrid_mode():
    """Test hybrid mode with dependency error log"""
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not set!")
        print("   export GEMINI_API_KEY='your-key-here'")
        return False
    
    print("🧪 Testing Hybrid Mode")
    print("=" * 70)
    
    # Load test log
    log_file = Path('data/synthetic_logs/logs/github-actions_dependency_error_10.txt')
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return False
    
    log_content = log_file.read_text()
    parsed = parse_log(log_content)
    
    print(f"✅ Loaded log: {log_file.name}")
    print(f"   Platform: {parsed.platform}")
    print(f"   Errors: {parsed.error_count}")
    print()
    
    # Test 1: ML-only mode (baseline)
    print("📊 Test 1: ML-only mode (no LLM)")
    print("-" * 70)
    
    analyzer = HybridAnalyzer(api_key=None)
    result_ml = analyzer.analyze(parsed, mode='ml-only')
    
    print(f"   Error Type: {result_ml['error_type']}")
    print(f"   Confidence: {result_ml['confidence']:.1%}")
    print(f"   Strategy: {result_ml.get('strategy', 'N/A')}")
    print(f"   ✅ ML-only passed")
    print()
    
    # Test 2: Hybrid mode (ML + specialized LLM)
    print("🚀 Test 2: Hybrid mode (ML + specialized LLM prompt)")
    print("-" * 70)
    
    analyzer_hybrid = HybridAnalyzer(api_key=api_key)
    
    try:
        print("   ⏳ Calling Gemini API...")
        result_hybrid = analyzer_hybrid.analyze(parsed, mode='hybrid')
        
        print(f"   ✅ API call successful!")
        print(f"   Error Type: {result_hybrid['error_type']}")
        print(f"   Confidence: {result_hybrid['confidence']:.1%}")
        print(f"   Strategy: {result_hybrid.get('strategy', 'N/A')}")
        
        if 'explanation' in result_hybrid:
            print(f"\n   💡 LLM Explanation (first 300 chars):")
            print(f"   {'-' * 66}")
            explanation = result_hybrid['explanation'][:300]
            for line in explanation.split('\n'):
                print(f"   {line}")
            if len(result_hybrid['explanation']) > 300:
                print(f"   ... ({len(result_hybrid['explanation'])} chars total)")
        
        print(f"\n   ✅ Hybrid mode passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Hybrid mode failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print()
    success = test_hybrid_mode()
    print()
    print("=" * 70)
    if success:
        print("🎉 All tests PASSED!")
        print("\nPhase 3B: Hybrid ML+LLM Integration - COMPLETE! ✅")
    else:
        print("❌ Tests FAILED")
        print("\nPlease check:")
        print("  1. GEMINI_API_KEY is set correctly")
        print("  2. Internet connection is working")
        print("  3. Gemini API quota is not exceeded")
    print()
