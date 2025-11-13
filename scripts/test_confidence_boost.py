#!/usr/bin/env python3
"""Test confidence boost with vucar log"""

from src.ml.predictor import ErrorClassifier

# Test log from vucar
log_vucar = """
node: error while loading shared libraries: libatomic.so.1: cannot open shared object file: No such file or directory
Stage "Code Quality" skipped due to earlier failure(s)
Stage "Lint" skipped due to earlier failure(s)
Failed in branch Lint
Failed in branch Type Check
"""

print("="*70)
print("Testing Confidence Boost")
print("="*70)

clf = ErrorClassifier()
result = clf.predict(log_vucar, 'jenkins')

print(f"\n📊 Results:")
print(f"Error Type: {result['error_type']}")
print(f"Base Confidence: {result.get('base_confidence', 'N/A'):.1%}")
print(f"Confidence Boost: +{result.get('confidence_boost', 0):.1%}")
print(f"Final Confidence: {result['confidence']:.1%}")

improvement = (result['confidence'] - result.get('base_confidence', result['confidence'])) * 100
print(f"\n✅ Improvement: +{improvement:.1f} percentage points")

if result.get('confidence_boost', 0) > 0:
    print(f"\n🎯 Boost triggered by strong signal detection:")
    print(f"   - 'shared librar' + '.so' pattern detected")
    print(f"   - System library dependency error confirmed")
