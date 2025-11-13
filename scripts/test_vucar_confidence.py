#!/usr/bin/env python3
"""Test vucar log confidence"""
import sys
sys.path.insert(0, '/Users/mac/projects/Thesis/ai-logguard/src')
from ml.predictor import ErrorClassifier

# Use realistic libatomic error with full context
log = """
npm WARN lifecycle vucar@1.0.0~build: cannot run in wd vucar@1.0.0 npm run build (wd=/app)
> vucar@1.0.0 build /app
> npm run build:prod

> vucar@1.0.0 build:prod /app
> webpack --config webpack.config.js --mode production

Hash: 1234567890abcdef
Version: webpack 4.46.0
Time: 15234ms
Built at: 2024-01-15 10:30:45
Asset      Size  Chunks             Chunk Names
main.js  1.2 MiB       0  [emitted]  main

ERROR in ./src/index.js
Module build failed (from ./node_modules/babel-loader/lib/index.js):
Error: cannot open shared object file: libatomic.so.1: cannot open shared object file: No such file or directory
    at Object.<anonymous> (/app/node_modules/@tensorflow/tfjs-node/lib/napi-v8/tfjs_binding.node:1:1)
    at Module._compile (internal/modules/cjs/loader.js:1137:30)
    at Object.Module._extensions..node (internal/modules/cjs/loader.js:1157:10)
    at Module.load (internal/modules/cjs/loader.js:985:32)
    at Function.Module._load (internal/modules/cjs/loader.js:878:14)
    at Module.require (internal/modules/cjs/loader.js:1025:19)

npm ERR! code ELIFECYCLE
npm ERR! errno 1
npm ERR! vucar@1.0.0 build:prod: `webpack --config webpack.config.js --mode production`
npm ERR! Exit status 1
"""

clf = ErrorClassifier()
result = clf.predict(log, 'jenkins')

print('=' * 60)
print('LIBATOMIC ERROR CONFIDENCE TEST')
print('=' * 60)
print(f"Error Type: {result['error_type']}")
print(f"Base Confidence: {result.get('base_confidence', result['confidence'])*100:.1f}%")
print(f"Boost: +{result.get('confidence_boost', 0)*100:.1f}%")
print(f"Final Confidence: {result['confidence']*100:.1f}%")
if 'detected_signals' in result and result['detected_signals']:
    print(f"\nDetected Signals:")
    for signal in result['detected_signals']:
        print(f"  • {signal}")
print(f"\nTop 3 Predictions:")
for cat, prob in list(result['probabilities'].items())[:3]:
    print(f"  {cat}: {prob*100:.1f}%")

