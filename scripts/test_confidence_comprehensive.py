#!/usr/bin/env python3
"""
Comprehensive test of confidence improvements
"""

from src.ml.predictor import ErrorClassifier

test_logs = {
    "System Library (libatomic)": """
    node: error while loading shared libraries: libatomic.so.1: cannot open shared object file: No such file or directory
    Stage "Code Quality" skipped due to earlier failure(s)
    """,
    
    "NPM Module Not Found": """
    npm ERR! code MODULE_NOT_FOUND
    npm ERR! Cannot find module 'react'
    npm ERR! A complete log of this run can be found in:
    """,
    
    "Python Import Error": """
    ModuleNotFoundError: No module named 'pandas'
    Traceback (most recent call last):
      File "app.py", line 5, in <module>
        import pandas as pd
    ImportError: No module named pandas
    """,
    
    "Syntax Error": """
    SyntaxError: Unexpected token '{'
      at Module._compile (internal/modules/cjs/loader.js:723:23)
    Expected '}' but found 'const'
    """,
    
    "Test Failure": """
    AssertionError: expected true to equal false
      at Context.<anonymous> (test/app.spec.js:45:23)
    Expected: { foo: 'bar' }
    Received: { foo: 'baz' }
    1 test failed, 5 passed
    """
}

clf = ErrorClassifier()

print("="*80)
print("CONFIDENCE BOOSTING TEST SUITE")
print("="*80)

results = []
for name, log in test_logs.items():
    result = clf.predict(log, 'jenkins')
    results.append({
        'name': name,
        'type': result['error_type'],
        'base': result.get('base_confidence', result['confidence']),
        'boost': result.get('confidence_boost', 0),
        'final': result['confidence'],
        'signals': result.get('detected_signals', [])
    })
    
    print(f"\n📝 {name}")
    print(f"   Type: {result['error_type']}")
    print(f"   Base: {result.get('base_confidence', result['confidence']):.1%}")
    print(f"   Boost: +{result.get('confidence_boost', 0):.1%}")
    print(f"   Final: {result['confidence']:.1%}")
    if result.get('detected_signals'):
        print(f"   Signals: {len(result['detected_signals'])}")
        for sig in result['detected_signals'][:3]:
            print(f"      • {sig}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

avg_base = sum(r['base'] for r in results) / len(results)
avg_final = sum(r['final'] for r in results) / len(results)
avg_boost = sum(r['boost'] for r in results) / len(results)

print(f"Average Base Confidence: {avg_base:.1%}")
print(f"Average Boost: +{avg_boost:.1%}")
print(f"Average Final Confidence: {avg_final:.1%}")
print(f"Overall Improvement: +{(avg_final - avg_base) * 100:.1f} percentage points")

high_conf = sum(1 for r in results if r['final'] >= 0.8)
print(f"\nHigh confidence (>=80%): {high_conf}/{len(results)} ({high_conf/len(results)*100:.0f}%)")
