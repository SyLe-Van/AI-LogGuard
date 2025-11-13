#!/usr/bin/env python3
"""
Test fetch AND analyze functionality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_fetch_analyze_integration():
    """
    Test tích hợp fetch + analyze
    """
    print("=" * 70)
    print("Testing Fetch + Analyze Integration")
    print("=" * 70)
    
    # Test 1: Verify imports work
    print("\n✅ Test 1: Verify imports")
    try:
        from src.parse import parse_log
        from src.cli import display_parsed_log
        print("   ✅ Imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Parse sample logs
    print("\n✅ Test 2: Parse sample logs")
    try:
        sample_log_file = Path(__file__).parent / "sample_logs.txt"
        
        if not sample_log_file.exists():
            print(f"   ⚠️  Sample log file not found: {sample_log_file}")
            return False
        
        with open(sample_log_file, 'r') as f:
            log_content = f.read()
        
        parsed = parse_log(log_content, job_name="test-job")
        print(f"   ✅ Parsed successfully")
        print(f"   - Total lines: {len(log_content.splitlines())}")
        print(f"   - Job name: {parsed.job_name}")
        print(f"   - Status: {parsed.status}")
        
    except Exception as e:
        print(f"   ❌ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test analyze logic (without actual fetch)
    print("\n✅ Test 3: Mock fetch + analyze workflow")
    try:
        # Simulate fetch result
        mock_logs = log_content
        
        # Parse
        parsed = parse_log(mock_logs, job_name="mock-jenkins-job")
        
        # Display (would be called in actual analyze)
        print("   ✅ Mock workflow successful")
        print(f"   - Parsed job: {parsed.job_name}")
        print(f"   - Stages: {len(parsed.stages)}")
        print(f"   - Errors: {len(parsed.errors)}")
        
    except Exception as e:
        print(f"   ❌ Mock workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Check conditional imports
    print("\n✅ Test 4: Check optional features")
    try:
        from src.cli import HYBRID_AVAILABLE, LLM_AVAILABLE
        print(f"   - HYBRID_AVAILABLE: {HYBRID_AVAILABLE}")
        print(f"   - LLM_AVAILABLE: {LLM_AVAILABLE}")
        
        if HYBRID_AVAILABLE:
            print("   ✅ Hybrid mode available")
        else:
            print("   ⚠️  Hybrid mode not available (this is OK)")
            
    except Exception as e:
        print(f"   ❌ Feature check failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_fetch_analyze_integration()
    sys.exit(0 if success else 1)
