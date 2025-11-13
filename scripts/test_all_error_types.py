#!/usr/bin/env python3
"""Test toàn diện confidence boosting cho TẤT CẢ error types"""
import sys
sys.path.insert(0, '/Users/mac/projects/Thesis/ai-logguard/src')
from ml.predictor import ErrorClassifier

test_cases = {
    "🐳 Docker Not Found (Vucar Real Log)": """
[Pipeline] sh
[2025-11-12T17:32:32.505Z] + docker build -t syle712/vucar-app:v1.0.6 .
[2025-11-12T17:32:32.505Z] /var/jenkins_home/workspace/vucar@tmp/durable-52ead777/script.sh.copy: 1: docker: not found
[Pipeline] }
ERROR: script returned exit code 127
Finished: FAILURE
""",

    "📦 System Library Missing (libatomic)": """
ERROR: cannot open shared object file: libatomic.so.1: cannot open shared object file: No such file or directory
at Object.<anonymous> (/app/node_modules/@tensorflow/tfjs-node/lib/napi-v8/tfjs_binding.node:1:1)
at Module._compile (internal/modules/cjs/loader.js:1137:30)
npm ERR! code ELIFECYCLE
npm ERR! errno 1
""",

    "📦 NPM Module Not Found": """
Error: Cannot find module 'express'
Require stack:
- /app/server.js
- /app/index.js
at Function.Module._resolveFilename (internal/modules/cjs/loader.js:880:15)
npm ERR! code ELIFECYCLE
npm ERR! errno 1
""",

    "🐍 Python Import Error": """
Traceback (most recent call last):
  File "main.py", line 5, in <module>
    import tensorflow as tf
ModuleNotFoundError: No module named 'tensorflow'
ERROR: Command returned non-zero exit code 1
""",

    "❌ Syntax Error (JavaScript)": """
/app/src/index.js:45:12
    const foo = {
              ^
SyntaxError: Unexpected token 'const'
    Expected '}' but found 'const'
    at Module._compile (internal/modules/cjs/loader.js:723:23)
""",

    "🧪 Test Failure": """
AssertionError: expected true to equal false
  at Context.<anonymous> (test/app.spec.js:45:23)
Expected: { foo: 'bar' }
Received: { foo: 'baz' }
1 test failed, 5 passed
npm test exited with code 1
""",

    "⏱️ Timeout Error": """
Error: Timeout of 30000ms exceeded
  at Test.Runnable._timeoutError (node_modules/mocha/lib/runnable.js:349:12)
  at Timeout.<anonymous> (node_modules/mocha/lib/runnable.js:356:10)
Build timed out (after 30 minutes). Marking the build as aborted.
""",

    "🌐 Network Error (Connection Refused)": """
Error: connect ECONNREFUSED 127.0.0.1:5432
    at TCPConnectWrap.afterConnect [as oncomplete] (net.js:1144:16)
Could not connect to database server
Connection refused by host
Build failed due to network issues
""",

    "🌐 DNS Resolution Failed": """
Error: getaddrinfo ENOTFOUND api.example.com
    at GetAddrInfoReqWrap.onlookup [as oncomplete] (dns.js:66:26)
Could not resolve host: api.example.com
Network unreachable
""",

    "🐳 Docker Pull Failed": """
Error response from daemon: pull access denied for myapp/image, repository does not exist or may require 'docker login'
failed to pull image myapp/image:latest
manifest for myapp/image:latest not found
Build failed at Docker step
""",
}

clf = ErrorClassifier()

print("=" * 100)
print("🚀 TEST TOÀN DIỆN CONFIDENCE BOOSTING - TẤT CẢ ERROR TYPES")
print("=" * 100)

results = []
for name, log in test_cases.items():
    result = clf.predict(log, 'jenkins')
    results.append({
        'name': name,
        'type': result['error_type'],
        'base': result.get('base_confidence', result['confidence']),
        'boost': result.get('confidence_boost', 0),
        'final': result['confidence'],
        'signals': result.get('detected_signals', []),
        'reclassified': result.get('reclassified', False),
        'original_type': result.get('original_error_type', None),
    })
    
    status = "✅" if result['confidence'] >= 0.80 else "⚠️" if result['confidence'] >= 0.60 else "❌"
    
    print(f"\n{status} {name}")
    print(f"   Type: {result['error_type']}")
    if result.get('reclassified'):
        print(f"   🔄 Reclassified from: {result['original_error_type']} ({result['original_confidence']*100:.1f}%)")
    print(f"   Base: {result.get('base_confidence', result['confidence'])*100:.1f}%")
    print(f"   Boost: +{result.get('confidence_boost', 0)*100:.1f}%")
    print(f"   Final: {result['confidence']*100:.1f}%")
    if result.get('detected_signals'):
        print(f"   Signals ({len(result['detected_signals'])}):")
        for signal in result['detected_signals'][:5]:
            print(f"      • {signal}")
        if len(result['detected_signals']) > 5:
            print(f"      ... and {len(result['detected_signals']) - 5} more")

print("\n" + "=" * 100)
print("📊 SUMMARY")
print("=" * 100)

avg_base = sum(r['base'] for r in results) / len(results)
avg_boost = sum(r['boost'] for r in results) / len(results)
avg_final = sum(r['final'] for r in results) / len(results)

print(f"\nAverage Base Confidence: {avg_base*100:.1f}%")
print(f"Average Boost: +{avg_boost*100:.1f}%")
print(f"Average Final Confidence: {avg_final*100:.1f}%")
print(f"Overall Improvement: +{(avg_final - avg_base)*100:.1f} percentage points")

high_conf = sum(1 for r in results if r['final'] >= 0.80)
medium_conf = sum(1 for r in results if 0.60 <= r['final'] < 0.80)
low_conf = sum(1 for r in results if r['final'] < 0.60)

print(f"\nHigh confidence (>=80%): {high_conf}/{len(results)} ({high_conf/len(results)*100:.0f}%)")
print(f"Medium confidence (60-79%): {medium_conf}/{len(results)} ({medium_conf/len(results)*100:.0f}%)")
print(f"Low confidence (<60%): {low_conf}/{len(results)} ({low_conf/len(results)*100:.0f}%)")

reclassified_count = sum(1 for r in results if r['reclassified'])
print(f"\nReclassified cases: {reclassified_count}/{len(results)} ({reclassified_count/len(results)*100:.0f}%)")
