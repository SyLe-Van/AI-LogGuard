#!/usr/bin/env python3
"""
Run Notebook 03: Model Training
Train Logistic Regression, Random Forest, and XGBoost models
"""
import sys
import os
import warnings
from pathlib import Path
from time import time

warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)
from sklearn.utils.class_weight import compute_sample_weight

# Try to import XGBoost (optional)
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not available, will use Random Forest as best model")

print("=" * 70)
print("🤖 NOTEBOOK 03: MODEL TRAINING")
print("=" * 70)

# ============================================================================
# 1. Load Features
# ============================================================================
print("\n📂 Loading features from Notebook 02...")

models_dir = project_root / "models"

try:
    X_train = joblib.load(models_dir / 'X_train.pkl')
    X_val = joblib.load(models_dir / 'X_val.pkl')
    X_test = joblib.load(models_dir / 'X_test.pkl')
    y_train = joblib.load(models_dir / 'y_train.pkl')
    y_val = joblib.load(models_dir / 'y_val.pkl')
    y_test = joblib.load(models_dir / 'y_test.pkl')

    label_encoder = joblib.load(models_dir / 'label_encoder.pkl')
    feature_info = joblib.load(models_dir / 'feature_info.pkl')

    print(f"✅ Features loaded!")
    print(f"   Train: {X_train.shape}")
    print(f"   Val:   {X_val.shape}")
    print(f"   Test:  {X_test.shape}")
    print(f"\n   Classes: {label_encoder.classes_.tolist()}")
except Exception as e:
    print(f"❌ Error loading features: {e}")
    print("   Please run notebook 02 first!")
    sys.exit(1)

# ============================================================================
# 2. Model 1: Logistic Regression (Baseline)
# ============================================================================
print("\n" + "=" * 70)
print("📊 MODEL 1: LOGISTIC REGRESSION (Baseline)")
print("=" * 70)

print("\n🔧 Training...")

lr_model = LogisticRegression(
    max_iter=1000,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

start = time()
lr_model.fit(X_train, y_train)
train_time = time() - start

print(f"✅ Training completed in {train_time:.2f}s")

# Predictions
y_train_pred = lr_model.predict(X_train)
y_val_pred = lr_model.predict(X_val)

# Evaluation
train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
val_f1 = f1_score(y_val, y_val_pred, average='weighted')

print(f"\n📊 Results:")
print(f"   Train Accuracy: {train_acc:.4f}")
print(f"   Val Accuracy:   {val_acc:.4f}")
print(f"   Val F1-Score:   {val_f1:.4f}")

lr_results = {
    'name': 'Logistic Regression',
    'model': lr_model,
    'train_acc': train_acc,
    'val_acc': val_acc,
    'val_f1': val_f1,
    'train_time': train_time
}

# ============================================================================
# 3. Model 2: Random Forest
# ============================================================================
print("\n" + "=" * 70)
print("🌲 MODEL 2: RANDOM FOREST")
print("=" * 70)

print("\n🔧 Training...")

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

start = time()
rf_model.fit(X_train, y_train)
train_time = time() - start

print(f"✅ Training completed in {train_time:.2f}s")

# Predictions
y_train_pred = rf_model.predict(X_train)
y_val_pred = rf_model.predict(X_val)

# Evaluation
train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
val_f1 = f1_score(y_val, y_val_pred, average='weighted')

print(f"\n📊 Results:")
print(f"   Train Accuracy: {train_acc:.4f}")
print(f"   Val Accuracy:   {val_acc:.4f}")
print(f"   Val F1-Score:   {val_f1:.4f}")

rf_results = {
    'name': 'Random Forest',
    'model': rf_model,
    'train_acc': train_acc,
    'val_acc': val_acc,
    'val_f1': val_f1,
    'train_time': train_time
}

# ============================================================================
# 4. Model 3: XGBoost (Best Performance) - Optional
# ============================================================================
if XGBOOST_AVAILABLE:
    print("\n" + "=" * 70)
    print("🚀 MODEL 3: XGBOOST (Best Performance)")
    print("=" * 70)

    print("\n🔧 Training...")

    # Calculate sample weights for imbalanced data
    sample_weights = compute_sample_weight('balanced', y_train)

    xgb_model = XGBClassifier(
        n_estimators=100,
        max_depth=10,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric='mlogloss'
    )

    start = time()
    xgb_model.fit(
        X_train, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    train_time = time() - start

    print(f"✅ Training completed in {train_time:.2f}s")

    # Predictions
    y_train_pred = xgb_model.predict(X_train)
    y_val_pred = xgb_model.predict(X_val)

    # Evaluation
    train_acc = accuracy_score(y_train, y_train_pred)
    val_acc = accuracy_score(y_val, y_val_pred)
    val_f1 = f1_score(y_val, y_val_pred, average='weighted')

    print(f"\n📊 Results:")
    print(f"   Train Accuracy: {train_acc:.4f}")
    print(f"   Val Accuracy:   {val_acc:.4f}")
    print(f"   Val F1-Score:   {val_f1:.4f}")

    xgb_results = {
        'name': 'XGBoost',
        'model': xgb_model,
        'train_acc': train_acc,
        'val_acc': val_acc,
        'val_f1': val_f1,
        'train_time': train_time
    }
else:
    print("\n⚠️  Skipping XGBoost (not available)")
    xgb_results = None
    xgb_model = None

# ============================================================================
# 5. Model Comparison
# ============================================================================
print("\n" + "=" * 70)
print("📊 MODEL COMPARISON")
print("=" * 70)

all_results = [lr_results, rf_results]
if xgb_results:
    all_results.append(xgb_results)

print("\n┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓")
print("┃ Model                 ┃ Train Acc ┃ Val Acc   ┃ Val F1    ┃ Time (s)  ┃")
print("┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩")

for r in all_results:
    print(f"│ {r['name']:21s} │ {r['train_acc']:9.4f} │ {r['val_acc']:9.4f} │ {r['val_f1']:9.4f} │ {r['train_time']:9.2f} │")

print("└───────────────────────┴───────────┴───────────┴───────────┴───────────┘")

# Find best model
best_result = max(all_results, key=lambda x: x['val_acc'])
print(f"\n🏆 Best Model: {best_result['name']} (Val Accuracy: {best_result['val_acc']:.4f})")

best_model = best_result['model']

# ============================================================================
# 6. Detailed Validation Report (Best Model)
# ============================================================================
print("\n" + "=" * 70)
print(f"📋 DETAILED VALIDATION REPORT - {best_result['name']}")
print("=" * 70)

y_val_pred = best_model.predict(X_val)

print("\n" + classification_report(y_val, y_val_pred, target_names=label_encoder.classes_))

# Confusion Matrix
print("\n📊 Confusion Matrix:")
cm = confusion_matrix(y_val, y_val_pred)

# Print confusion matrix
header = "     " + " ".join(f"{cls[:4]:>4s}" for cls in label_encoder.classes_)
print(header)
print("     " + "─" * len(header))

for i, true_label in enumerate(label_encoder.classes_):
    row = f"{true_label[:4]:>4s} │"
    for j in range(len(label_encoder.classes_)):
        row += f" {cm[i, j]:3d} "
    print(row)

# Per-class accuracy
print("\n📊 Per-Class Accuracy:")
for i, label in enumerate(label_encoder.classes_):
    class_acc = cm[i, i] / cm[i].sum() if cm[i].sum() > 0 else 0
    print(f"   {label:25s}: {class_acc:6.2%} ({cm[i, i]:2d}/{cm[i].sum():2d})")

# ============================================================================
# 7. Test Set Evaluation (Final)
# ============================================================================
print("\n" + "=" * 70)
print("🧪 TEST SET EVALUATION (Final)")
print("=" * 70)

y_test_pred = best_model.predict(X_test)
test_acc = accuracy_score(y_test, y_test_pred)
test_f1 = f1_score(y_test, y_test_pred, average='weighted')

print(f"\n✅ Test Results:")
print(f"   Accuracy:  {test_acc:.4f}")
print(f"   F1-Score:  {test_f1:.4f}")

print("\n" + classification_report(y_test, y_test_pred, target_names=label_encoder.classes_))

# ============================================================================
# 8. Feature Importance (Top 20)
# ============================================================================
if best_result['name'] in ['XGBoost', 'Random Forest']:
    print("\n" + "=" * 70)
    print("🔝 TOP 20 MOST IMPORTANT FEATURES")
    print("=" * 70)

    # Get feature importances
    feature_importance = best_model.feature_importances_

    # Get top 20
    top_n = 20
    top_indices = np.argsort(feature_importance)[-top_n:][::-1]
    top_scores = feature_importance[top_indices]

    # Get feature names
    tfidf = joblib.load(models_dir / 'tfidf_vectorizer.pkl')
    tfidf_features = tfidf.get_feature_names_out().tolist()
    structural_features = feature_info['structural_feature_names']
    platform_features = feature_info['platform_feature_names']

    all_feature_names = tfidf_features + structural_features + platform_features
    top_feature_names = [all_feature_names[i] for i in top_indices]

    print()
    for i, (name, score) in enumerate(zip(top_feature_names, top_scores), 1):
        print(f"   {i:2d}. {name:40s} : {score:.6f}")

# ============================================================================
# 9. Inference Speed Test
# ============================================================================
print("\n" + "=" * 70)
print("⏱️  INFERENCE SPEED TEST")
print("=" * 70)

import time as time_module

print()

# Convert to CSR format for efficient slicing
X_test_csr = X_test.tocsr() if hasattr(X_test, 'tocsr') else X_test

for result in all_results:
    model = result['model']
    name = result['name']

    # Single prediction
    start = time_module.time()
    _ = model.predict(X_test_csr[0:1])
    single_time = (time_module.time() - start) * 1000  # ms

    # Batch prediction (10 samples)
    start = time_module.time()
    _ = model.predict(X_test_csr[:10])
    batch_time = (time_module.time() - start) * 1000  # ms

    print(f"{name}:")
    print(f"   Single prediction: {single_time:6.2f} ms")
    print(f"   Batch (10):        {batch_time:6.2f} ms ({batch_time/10:5.2f} ms/sample)")
    print()

target_met = single_time < 100
status = "✅ EXCELLENT!" if target_met else "⚠️  Acceptable (< 1s)"
print(f"Target: < 100ms for real-time CLI → {status}")

# ============================================================================
# 10. Save Models
# ============================================================================
print("\n" + "=" * 70)
print("💾 SAVING MODELS")
print("=" * 70)

print()
if xgb_model:
    joblib.dump(xgb_model, models_dir / 'error_classifier_xgb.pkl')
    print("✅ Saved: error_classifier_xgb.pkl")

joblib.dump(rf_model, models_dir / 'error_classifier_rf.pkl')
print("✅ Saved: error_classifier_rf.pkl")

joblib.dump(lr_model, models_dir / 'error_classifier_lr.pkl')
print("✅ Saved: error_classifier_lr.pkl")

# Save model metadata
model_metadata = {
    'best_model': best_result['name'],
    'best_model_file': f"error_classifier_{best_result['name'].lower().replace(' ', '_')}.pkl",
    'test_accuracy': test_acc,
    'test_f1_score': test_f1,
    'val_accuracy': best_result['val_acc'],
    'val_f1_score': best_result['val_f1'],
    'classes': label_encoder.classes_.tolist(),
    'num_features': X_train.shape[1],
    'training_samples': len(y_train),
    'inference_time_ms': single_time,
}

joblib.dump(model_metadata, models_dir / 'model_metadata.pkl')
print("✅ Saved: model_metadata.pkl")

print("\n" + "=" * 70)
print("✅ NOTEBOOK 03 COMPLETE!")
print("=" * 70)

print(f"\n📊 Final Results:")
print(f"   🏆 Best Model: {best_result['name']}")
print(f"   🎯 Test Accuracy: {test_acc:.2%}")
print(f"   📈 Test F1-Score: {test_f1:.4f}")
print(f"   ⚡ Inference Time: {single_time:.2f} ms")

print(f"\n📁 Models saved to: {models_dir}")
print(f"\n➡️  Next: Integrate classifier into CLI (src/ml/classifier.py)")
