#!/usr/bin/env python3
"""Debug vucar confidence - Phân tích chi tiết tại sao confidence thấp"""
import sys
import requests
sys.path.insert(0, '/Users/mac/projects/Thesis/ai-logguard/src')
from ml.predictor import ErrorClassifier

# Fetch vucar log từ Jenkins
url = "http://localhost:8080/job/vucar/lastBuild/consoleText"
headers = {'Authorization': 'Basic ' + 'admin:111368d8be4f2289b2e65bae4f4cb6537a'.encode().hex()}

try:
    response = requests.get(url, timeout=10)
    log_full = response.text
    
    print("=" * 80)
    print("📊 PHÂN TÍCH CHI TIẾT CONFIDENCE - VUCAR LOG")
    print("=" * 80)
    print(f"\n📝 Log length: {len(log_full)} characters")
    print(f"📝 Log lines: {len(log_full.splitlines())} lines")
    
    # Test với nhiều độ dài log khác nhau
    test_lengths = [
        ("Full log", log_full),
        ("Last 5000 chars", log_full[-5000:]),
        ("Last 2000 chars", log_full[-2000:]),
        ("Last 1000 chars", log_full[-1000:]),
        ("Last 500 chars", log_full[-500:]),
    ]
    
    clf = ErrorClassifier()
    
    print("\n" + "=" * 80)
    print("🔍 TEST VỚI NHIỀU ĐỘ DÀI LOG")
    print("=" * 80)
    
    for name, log in test_lengths:
        result = clf.predict(log, 'jenkins')
        
        print(f"\n📌 {name} ({len(log)} chars):")
        print(f"   Error Type: {result['error_type']}")
        print(f"   Base Confidence: {result.get('base_confidence', result['confidence'])*100:.1f}%")
        print(f"   Boost: +{result.get('confidence_boost', 0)*100:.1f}%")
        print(f"   Final Confidence: {result['confidence']*100:.1f}%")
        
        if 'detected_signals' in result and result['detected_signals']:
            print(f"   Signals ({len(result['detected_signals'])}):")
            for signal in result['detected_signals']:
                print(f"      • {signal}")
        else:
            print(f"   ⚠️  No signals detected!")
        
        print(f"   Top 3 predictions:")
        for i, (cat, prob) in enumerate(list(result['probabilities'].items())[:3], 1):
            print(f"      {i}. {cat}: {prob*100:.1f}%")
    
    # Phân tích nội dung log để tìm patterns
    print("\n" + "=" * 80)
    print("🔍 PHÂN TÍCH PATTERNS TRONG LOG")
    print("=" * 80)
    
    log_lower = log_full.lower()
    
    patterns_to_check = {
        'Dependency Patterns': [
            ('shared librar', 'System library error'),
            ('.so', 'Shared object file'),
            ('libatomic', 'libatomic specifically'),
            ('cannot open shared object', 'Cannot open shared object'),
            ('module not found', 'Module not found'),
            ('cannot find module', 'Cannot find module'),
            ('npm err', 'NPM error'),
            ('no such file or directory', 'File not found'),
        ],
        'Error Type Patterns': [
            ('error', 'Generic error'),
            ('failed', 'Failed'),
            ('exit code', 'Exit code'),
            ('exception', 'Exception'),
        ],
        'Build Patterns': [
            ('webpack', 'Webpack'),
            ('babel', 'Babel'),
            ('build', 'Build'),
            ('compile', 'Compile'),
        ]
    }
    
    for category, patterns in patterns_to_check.items():
        print(f"\n📂 {category}:")
        found_any = False
        for pattern, description in patterns:
            count = log_lower.count(pattern)
            if count > 0:
                print(f"   ✅ '{pattern}': {count} occurrences - {description}")
                found_any = True
        if not found_any:
            print(f"   ❌ No patterns found")
    
    # Trích xuất error lines
    print("\n" + "=" * 80)
    print("🔍 ERROR LINES")
    print("=" * 80)
    
    error_lines = [line for line in log_full.splitlines() if 'error' in line.lower()]
    print(f"\nFound {len(error_lines)} error lines:")
    for i, line in enumerate(error_lines[:10], 1):
        print(f"{i}. {line.strip()[:100]}")
    if len(error_lines) > 10:
        print(f"... and {len(error_lines) - 10} more error lines")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
