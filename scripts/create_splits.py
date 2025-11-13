#!/usr/bin/env python3
"""
Create train/val/test splits from synthetic logs dataset
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sklearn.model_selection import train_test_split

print("=" * 70)
print("📊 CREATING TRAIN/VAL/TEST SPLITS")
print("=" * 70)

# Load dataset
data_dir = project_root / "data" / "synthetic_logs"
dataset_path = data_dir / "dataset.csv"

if not dataset_path.exists():
    print(f"❌ Dataset not found at {dataset_path}")
    sys.exit(1)

print(f"\n📂 Loading dataset from: {dataset_path}")
df = pd.read_csv(dataset_path)

print(f"✅ Loaded {len(df)} samples")
print(f"\n📊 Dataset info:")
print(f"   Platforms: {df['platform'].value_counts().to_dict()}")
print(f"   Error categories: {df['error_category'].value_counts().to_dict()}")

# Update file paths to absolute paths
print("\n🔧 Updating file paths to absolute...")
df['file_path'] = df['file_path'].apply(lambda x: str(data_dir / x))

# Verify files exist
missing = 0
for path in df['file_path'].head(10):  # Check first 10
    if not Path(path).exists():
        missing += 1
        print(f"   ⚠️  Missing: {path}")

if missing > 0:
    print(f"\n⚠️  Warning: {missing}/10 sampled files not found")
    print("   Continuing anyway...")

# Stratified split: 70% train, 15% val, 15% test
print("\n🔧 Creating stratified splits...")

# First split: 70% train, 30% temp
train_df, temp_df = train_test_split(
    df,
    test_size=0.3,
    stratify=df['error_category'],
    random_state=42
)

# Second split: 15% val, 15% test (from 30% temp)
val_df, test_df = train_test_split(
    temp_df,
    test_size=0.5,
    stratify=temp_df['error_category'],
    random_state=42
)

print(f"✅ Splits created:")
print(f"   Train: {len(train_df)} samples ({len(train_df)/len(df)*100:.1f}%)")
print(f"   Val:   {len(val_df)} samples ({len(val_df)/len(df)*100:.1f}%)")
print(f"   Test:  {len(test_df)} samples ({len(test_df)/len(df)*100:.1f}%)")

# Show distribution
print(f"\n📊 Error category distribution:")
print("\nTrain:")
print(train_df['error_category'].value_counts().sort_index())
print("\nVal:")
print(val_df['error_category'].value_counts().sort_index())
print("\nTest:")
print(test_df['error_category'].value_counts().sort_index())

# Save splits
print(f"\n💾 Saving splits to {data_dir}")
train_df.to_csv(data_dir / 'train.csv', index=False)
val_df.to_csv(data_dir / 'val.csv', index=False)
test_df.to_csv(data_dir / 'test.csv', index=False)

print("✅ Saved:")
print(f"   - {data_dir / 'train.csv'}")
print(f"   - {data_dir / 'val.csv'}")
print(f"   - {data_dir / 'test.csv'}")

print("\n" + "=" * 70)
print("✅ SPLITS CREATED SUCCESSFULLY!")
print("=" * 70)
print("\n➡️  Next: Run notebook 02 (Feature Engineering)")
