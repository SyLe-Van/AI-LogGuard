#!/usr/bin/env python3
"""Test confidence với vucar log thực tế (docker not found)"""
import sys
sys.path.insert(0, '/Users/mac/projects/Thesis/ai-logguard/src')
from ml.predictor import ErrorClassifier

# Log thực tế từ vucar - FULL LOG để có context tốt hơn
vucar_log = """
Started by user Sy Le
Obtained Jenkinsfile from git https://github.com/SyLe-Van/Vucar---Inspection-Car-App
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/vucar
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Declarative: Checkout SCM)
[Pipeline] checkout
Selected Git installation does not exist. Using Default
The recommended git tool is: NONE
using credential github-token
Cloning the remote Git repository
Cloning repository https://github.com/SyLe-Van/Vucar---Inspection-Car-App
 > git init /var/jenkins_home/workspace/vucar # timeout=10
Fetching upstream changes from https://github.com/SyLe-Van/Vucar---Inspection-Car-App
 > git --version # timeout=10
 > git --version # 'git version 2.39.5'
using GIT_ASKPASS to set credentials GitHub Personal Access Token
 > git fetch --tags --force --progress -- https://github.com/SyLe-Van/Vucar---Inspection-Car-App +refs/heads/*:refs/remotes/origin/* # timeout=10
 > git config remote.origin.url https://github.com/SyLe-Van/Vucar---Inspection-Car-App # timeout=10
 > git config --add remote.origin.fetch +refs/heads/*:refs/remotes/origin/* # timeout=10
Avoid second fetch
 > git rev-parse refs/remotes/origin/main^{commit} # timeout=10
Checking out Revision d5126d95442ade390de0c04ab0450fa2ab63172f (refs/remotes/origin/main)
 > git config core.sparsecheckout # timeout=10
 > git checkout -f d5126d95442ade390de0c04ab0450fa2ab63172f # timeout=10
Commit message: "fix: đồng bộ biến môi trường MONGODB_URI cho rebuild-car-index.js và các script"
 > git rev-list --no-walk d5126d95442ade390de0c04ab0450fa2ab63172f # timeout=10
[Pipeline] }
[Pipeline] // stage
[Pipeline] withEnv
[Pipeline] {
[Pipeline] withEnv
[Pipeline] {
[Pipeline] timeout
Timeout set to expire in 30 min
[Pipeline] {
[Pipeline] timestamps
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Declarative: Tool Install)
[Pipeline] tool
[Pipeline] envVarsForTool
[Pipeline] }
[Pipeline] // stage
[Pipeline] withEnv
[Pipeline] {
[Pipeline] stage
[Pipeline] { (🔍 Branch Check)
[Pipeline] tool
[Pipeline] envVarsForTool
[Pipeline] withEnv
[Pipeline] {
[Pipeline] script
[Pipeline] {
[Pipeline] echo
[2025-11-12T17:30:39.834Z] Current branch: origin/main
[Pipeline] echo
[2025-11-12T17:30:39.845Z] ✅ Main branch detected - continuing pipeline
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (🐳 Build Docker Image)
[Pipeline] tool
[Pipeline] envVarsForTool
[Pipeline] withEnv
[Pipeline] {
[Pipeline] script
[Pipeline] {
[Pipeline] echo
[2025-11-12T17:32:31.208Z] 🐳 Building Docker image
[Pipeline] isUnix
[Pipeline] withEnv
[Pipeline] {
[Pipeline] sh
[2025-11-12T17:32:32.505Z] + docker build -t syle712/vucar-app:v1.0.6 .
[2025-11-12T17:32:32.505Z] /var/jenkins_home/workspace/vucar@tmp/durable-52ead777/script.sh.copy: 1: docker: not found
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (📤 Push Docker Image)
Stage "📤 Push Docker Image" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
[Pipeline] // stage
[Pipeline] echo
[2025-11-12T17:32:33.431Z] ❌ Pipeline failed!
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // timestamps
[Pipeline] }
[Pipeline] // timeout
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
ERROR: script returned exit code 127
Finished: FAILURE
"""

clf = ErrorClassifier()
result = clf.predict(vucar_log, 'jenkins')

print('=' * 80)
print('🚀 VUCAR LOG - DOCKER NOT FOUND ERROR')
print('=' * 80)
print(f"\n📊 Classification Result:")
print(f"   Error Type: {result['error_type']}")
print(f"   Base Confidence: {result.get('base_confidence', result['confidence'])*100:.1f}%")
print(f"   Boost: +{result.get('confidence_boost', 0)*100:.1f}%")
print(f"   Final Confidence: {result['confidence']*100:.1f}%")

if 'detected_signals' in result and result['detected_signals']:
    print(f"\n🔍 Detected Signals ({len(result['detected_signals'])}):")
    for signal in result['detected_signals']:
        print(f"   • {signal}")
else:
    print(f"\n⚠️  No signals detected!")

print(f"\n📈 Top 5 Predictions:")
for i, (cat, prob) in enumerate(list(result['probabilities'].items())[:5], 1):
    bar = '█' * int(prob * 50)
    print(f"   {i}. {cat:20s} {prob*100:5.1f}% {bar}")
