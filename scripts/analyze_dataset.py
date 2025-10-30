"""
Quick analysis of synthetic dataset
Verify quality and distribution (no pandas required)
"""

import json
import csv
from pathlib import Path
from collections import Counter


def analyze_dataset(dataset_path: str = "data/synthetic_logs"):
    """Analyze synthetic dataset"""
    
    print("=" * 70)
    print("📊 SYNTHETIC DATASET ANALYSIS")
    print("=" * 70)
    
    # Load metadata from CSV
    with open(f"{dataset_path}/dataset.csv") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    print(f"\n📁 Total Logs: {len(data)}")
    
    # Error category distribution
    print("\n🏷️  ERROR CATEGORY DISTRIBUTION:")
    print("-" * 70)
    categories = Counter([row['error_category'] for row in data])
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(data)) * 100
        bar = "█" * int(percentage / 2)
        print(f"{category:25s} {count:3d} ({percentage:5.1f}%) {bar}")
    
    # Platform distribution
    print("\n🔧 PLATFORM DISTRIBUTION:")
    print("-" * 70)
    platforms = Counter([row['platform'] for row in data])
    for platform, count in sorted(platforms.items()):
        percentage = (count / len(data)) * 100
        print(f"{platform:20s} {count:3d} ({percentage:5.1f}%)")
    
    # Cross-tabulation
    print("\n📊 ERROR TYPES BY PLATFORM:")
    print("-" * 70)
    cross_tab = {}
    for row in data:
        cat = row['error_category']
        plat = row['platform']
        if cat not in cross_tab:
            cross_tab[cat] = {}
        cross_tab[cat][plat] = cross_tab[cat].get(plat, 0) + 1
    
    # Print cross-tab
    all_platforms = sorted(platforms.keys())
    print(f"{'Error Category':<25s} " + " ".join([f"{p:<12s}" for p in all_platforms]))
    print("-" * 70)
    for cat in sorted(cross_tab.keys()):
        counts = [str(cross_tab[cat].get(p, 0)) for p in all_platforms]
        print(f"{cat:<25s} " + " ".join([f"{c:<12s}" for c in counts]))
    
    # Sample logs
    print("\n📝 SAMPLE LOGS (first 3):")
    print("-" * 70)
    for idx in range(min(3, len(data))):
        row = data[idx]
        print(f"\n{idx+1}. {row['log_id']}")
        print(f"   Platform: {row['platform']}")
        print(f"   Category: {row['error_category']}")
        
        # Read log file
        log_file = Path(dataset_path) / row['file_path']
        if log_file.exists():
            content = log_file.read_text()
            lines = content.split('\n')
            print(f"   Lines: {len(lines)}")
            print(f"   Preview (first 5 lines):")
            for line in lines[:5]:
                print(f"      {line}")
    
    # Verify balance
    print("\n✅ DATASET QUALITY CHECK:")
    print("-" * 70)
    
    # Check class balance
    counts = list(categories.values())
    min_count = min(counts)
    max_count = max(counts)
    balance_ratio = min_count / max_count
    
    print(f"Min samples per class: {min_count}")
    print(f"Max samples per class: {max_count}")
    print(f"Balance ratio: {balance_ratio:.2f}")
    
    if balance_ratio >= 0.7:
        print("✅ Well balanced!")
    elif balance_ratio >= 0.5:
        print("⚠️  Moderately balanced")
    else:
        print("❌ Imbalanced - consider rebalancing")
    
    # Recommended splits
    print("\n📊 RECOMMENDED TRAIN/VAL/TEST SPLIT (70/15/15):")
    print("-" * 70)
    print(f"Train: {int(len(data) * 0.7)} samples")
    print(f"Val:   {int(len(data) * 0.15)} samples")
    print(f"Test:  {int(len(data) * 0.15)} samples")
    
    # Load statistics
    stats_file = Path(dataset_path) / "statistics.json"
    if stats_file.exists():
        with open(stats_file) as f:
            stats = json.load(f)
        
        print("\n📈 STATISTICS FROM statistics.json:")
        print("-" * 70)
        print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    analyze_dataset()
