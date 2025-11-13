#!/usr/bin/env python3
"""
Run Notebook 02: Feature Engineering
Extracts features from synthetic logs for ML training
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

import pandas as pd
import numpy as np
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import hstack

print("=" * 70)
print("🔧 NOTEBOOK 02: FEATURE ENGINEERING")
print("=" * 70)

# ============================================================================
# 1. Setup
# ============================================================================
print("\n📦 Setup...")
print("✅ Libraries imported!")

# ============================================================================
# 2. Load Data
# ============================================================================
print("\n📂 Loading data splits...")

# Check if we need to load from cloned repo
data_dir = project_root / "data" / "synthetic_logs"
if not data_dir.exists():
    print(f"⚠️  Data not found at {data_dir}")
    print("Looking in notebooks/AI-LogGuard...")
    data_dir = project_root / "notebooks" / "AI-LogGuard" / "data" / "synthetic_logs"

if not data_dir.exists():
    print(f"❌ Data directory not found!")
    print(f"Please run notebook 01 first to download the dataset")
    sys.exit(1)

train_df = pd.read_csv(data_dir / 'train.csv')
val_df = pd.read_csv(data_dir / 'val.csv')
test_df = pd.read_csv(data_dir / 'test.csv')

print(f"✅ Data loaded!")
print(f"   Train: {len(train_df)} samples")
print(f"   Val:   {len(val_df)} samples")
print(f"   Test:  {len(test_df)} samples")

# ============================================================================
# 3. Load Log Contents
# ============================================================================
print("\n📂 Loading log contents...")

def load_log_content(file_path):
    """Load content from log file"""
    try:
        # Try different base paths
        if Path(file_path).exists():
            path = Path(file_path)
        else:
            # Try relative to data_dir
            path = data_dir / file_path
            if not path.exists():
                # Try without 'logs/' prefix
                path = data_dir / Path(file_path).name

        if not path.exists():
            print(f"⚠️  File not found: {file_path}")
            return ""

        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return ""

# Load log contents
train_df['log_content'] = train_df['file_path'].apply(load_log_content)
val_df['log_content'] = val_df['file_path'].apply(load_log_content)
test_df['log_content'] = test_df['file_path'].apply(load_log_content)

# Check if logs were loaded
loaded_count = (train_df['log_content'].str.len() > 0).sum()
print(f"✅ Log contents loaded! ({loaded_count}/{len(train_df)} files)")

if loaded_count == 0:
    print("❌ No log files loaded! Check file paths.")
    sys.exit(1)

print(f"\n📄 Sample log (first 300 chars):")
print(train_df['log_content'].iloc[0][:300])

# ============================================================================
# 4. Text Preprocessing
# ============================================================================
print("\n🔧 Preprocessing text...")

def preprocess_text(text):
    """Clean and preprocess log text"""
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove timestamps (common patterns)
    text = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', '', text)
    text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)

    # Remove URLs
    text = re.sub(r'https?://\S+', 'URL', text)

    # Remove file paths (but keep file names)
    text = re.sub(r'/[a-z0-9_\-/]+/', ' ', text)

    # Remove build numbers
    text = re.sub(r'#\d+', '', text)

    # Remove version numbers (keep semantic meaning)
    text = re.sub(r'\d+\.\d+\.\d+', 'VERSION', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# Apply preprocessing
train_df['log_clean'] = train_df['log_content'].apply(preprocess_text)
val_df['log_clean'] = val_df['log_content'].apply(preprocess_text)
test_df['log_clean'] = test_df['log_content'].apply(preprocess_text)

print("✅ Preprocessing complete!")

# ============================================================================
# 5. TF-IDF Features
# ============================================================================
print("\n🔧 Creating TF-IDF features...")

tfidf = TfidfVectorizer(
    max_features=500,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.8,
    sublinear_tf=True
)

# Fit on training data only!
X_train_tfidf = tfidf.fit_transform(train_df['log_clean'])
X_val_tfidf = tfidf.transform(val_df['log_clean'])
X_test_tfidf = tfidf.transform(test_df['log_clean'])

print(f"✅ TF-IDF features created!")
print(f"   Feature matrix shape: {X_train_tfidf.shape}")
print(f"   Vocabulary size: {len(tfidf.vocabulary_)}")

# Show top features
feature_names = tfidf.get_feature_names_out()
print(f"\n🔝 Top 30 TF-IDF features:")
print(feature_names[:30])

# ============================================================================
# 6. Structural Features
# ============================================================================
print("\n🔧 Extracting structural features...")

def extract_structural_features(row):
    """Extract structural features from log"""
    content = row['log_content']

    features = {
        # Length features
        'log_length': len(content),
        'num_lines': content.count('\n'),

        # Error patterns
        'has_error_keyword': int(bool(re.search(r'\berror\b', content, re.I))),
        'has_failed_keyword': int(bool(re.search(r'\bfailed\b', content, re.I))),
        'has_exception': int(bool(re.search(r'\bexception\b', content, re.I))),
        'has_timeout': int(bool(re.search(r'\btimeout\b|\btimed out\b', content, re.I))),

        # Error code patterns
        'has_npm_error': int(bool(re.search(r'\bERR!\b|\bE[A-Z]+\b', content))),
        'has_pip_error': int(bool(re.search(r'\bERROR:\b', content))),
        'has_ts_error': int(bool(re.search(r'\bTS\d+\b', content))),
        'has_syntax_error': int(bool(re.search(r'SyntaxError|IndentationError', content))),

        # Test patterns
        'has_test_failed': int(bool(re.search(r'\btest.*failed\b|\bfailed.*test\b', content, re.I))),
        'has_assertion_error': int(bool(re.search(r'AssertionError|expect.*received', content))),

        # Stack trace
        'has_stack_trace': int(bool(re.search(r'\s+at\s+.*\(.*:\d+:\d+\)', content))),

        # Exit codes
        'has_exit_code': int(bool(re.search(r'exit code|exit status', content, re.I))),
    }

    return pd.Series(features)

# Extract structural features
train_struct = train_df.apply(extract_structural_features, axis=1)
val_struct = val_df.apply(extract_structural_features, axis=1)
test_struct = test_df.apply(extract_structural_features, axis=1)

print("✅ Structural features extracted!")
print(f"   Features: {list(train_struct.columns)}")

# ============================================================================
# 7. Platform Features
# ============================================================================
print("\n🔧 Encoding platform features...")

platform_dummies_train = pd.get_dummies(train_df['platform'], prefix='platform')
platform_dummies_val = pd.get_dummies(val_df['platform'], prefix='platform')
platform_dummies_test = pd.get_dummies(test_df['platform'], prefix='platform')

print(f"✅ Platform features: {platform_dummies_train.columns.tolist()}")

# ============================================================================
# 8. Combine All Features
# ============================================================================
print("\n🔧 Combining all features...")

X_train = hstack([
    X_train_tfidf,
    train_struct.values,
    platform_dummies_train.values
])

X_val = hstack([
    X_val_tfidf,
    val_struct.values,
    platform_dummies_val.values
])

X_test = hstack([
    X_test_tfidf,
    test_struct.values,
    platform_dummies_test.values
])

print(f"✅ Combined features!")
print(f"   Train shape: {X_train.shape}")
print(f"   Val shape:   {X_val.shape}")
print(f"   Test shape:  {X_test.shape}")

# ============================================================================
# 9. Prepare Labels
# ============================================================================
print("\n🔧 Encoding labels...")

label_encoder = LabelEncoder()
y_train = label_encoder.fit_transform(train_df['error_category'])
y_val = label_encoder.transform(val_df['error_category'])
y_test = label_encoder.transform(test_df['error_category'])

print("✅ Label encoding:")
for i, label in enumerate(label_encoder.classes_):
    print(f"   {i}: {label}")

print(f"\n📊 Label distribution in train set:")
unique, counts = np.unique(y_train, return_counts=True)
for label_id, count in zip(unique, counts):
    print(f"   {label_encoder.classes_[label_id]}: {count}")

# ============================================================================
# 10. Save Features & Preprocessors
# ============================================================================
print("\n💾 Saving features and preprocessors...")

models_dir = project_root / "models"
models_dir.mkdir(exist_ok=True)

# Save features
joblib.dump(X_train, models_dir / 'X_train.pkl')
joblib.dump(X_val, models_dir / 'X_val.pkl')
joblib.dump(X_test, models_dir / 'X_test.pkl')
joblib.dump(y_train, models_dir / 'y_train.pkl')
joblib.dump(y_val, models_dir / 'y_val.pkl')
joblib.dump(y_test, models_dir / 'y_test.pkl')

# Save preprocessors
joblib.dump(tfidf, models_dir / 'tfidf_vectorizer.pkl')
joblib.dump(label_encoder, models_dir / 'label_encoder.pkl')

# Save feature info
feature_info = {
    'tfidf_features': X_train_tfidf.shape[1],
    'structural_features': len(train_struct.columns),
    'platform_features': len(platform_dummies_train.columns),
    'total_features': X_train.shape[1],
    'structural_feature_names': train_struct.columns.tolist(),
    'platform_feature_names': platform_dummies_train.columns.tolist()
}
joblib.dump(feature_info, models_dir / 'feature_info.pkl')

print("\n✅ All saved!")
print(f"   📁 Output directory: {models_dir}")
print("   Files created:")
print("      - X_train.pkl, X_val.pkl, X_test.pkl")
print("      - y_train.pkl, y_val.pkl, y_test.pkl")
print("      - tfidf_vectorizer.pkl")
print("      - label_encoder.pkl")
print("      - feature_info.pkl")

# ============================================================================
# 11. Feature Analysis
# ============================================================================
print("\n📊 Feature statistics by error category:")

for col in train_struct.columns[:5]:
    print(f"\n{col}:")
    combined = pd.concat([train_df['error_category'], train_struct[col]], axis=1)
    stats = combined.groupby('error_category')[col].mean().sort_values(ascending=False)
    for cat, val in stats.head(3).items():
        print(f"   {cat}: {val:.2f}")

print("\n" + "=" * 70)
print("✅ NOTEBOOK 02 COMPLETE!")
print("=" * 70)
print("\n➡️  Next: Run notebook 03 (Model Training)")
