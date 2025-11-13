# 🚀 Phase 3 Quick Start Guide

## Overview

Hướng dẫn nhanh để chạy Phase 3 notebooks (ML Model Training) cho AI-LogGuard.

---

## 📋 Prerequisites

### 1. Environment Setup

```bash
# Ensure you're in project root
cd /Users/mac/projects/Thesis/ai-logguard

# Verify Python version (3.9+)
python --version

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install ML-specific packages
pip install pandas numpy matplotlib seaborn scikit-learn xgboost joblib scipy
```

### 2. Dataset Verification

```bash
# Check if dataset exists
ls -la data/synthetic_logs/

# Should see:
# - dataset.csv
# - statistics.json
# - Log files in subdirectories
```

**If dataset is missing:**
- Refer to dataset generation scripts (Phase 1)
- Or download sample dataset from repository

---

## 🔧 Step 1: Fix Notebooks (One-time)

Before running notebooks for the first time, apply automatic fixes:

```bash
# Run the fix script
python scripts/fix_notebooks.py

# This will:
# ✅ Remove git clone from notebook 01
# ✅ Fix path issues in notebook 05
# ✅ Add variable validation to notebooks 04 & 05
# ✅ Validate your environment
```

**Output should show:**
```
✅ ALL FIXES APPLIED SUCCESSFULLY
```

---

## 📓 Step 2: Run Notebooks in Order

### Method 1: Jupyter Notebook (Recommended)

```bash
# Start Jupyter from project root
jupyter notebook

# Or use Jupyter Lab
jupyter lab

# Navigate to notebooks/ and run in order:
# 1. 01_dataset_exploration.ipynb
# 2. 02_feature_engineering.ipynb
# 3. 03_model_training.ipynb
# 4. 04_model_evaluation.ipynb
# 5. 05_production_integration.ipynb
```

### Method 2: VS Code

```bash
# Open VS Code
code .

# Install Jupyter extension if not installed
# Open notebooks in VS Code
# Run cells one by one or "Run All"
```

### Method 3: Command Line (nbconvert)

```bash
# Convert and execute notebooks
jupyter nbconvert --to notebook --execute notebooks/01_dataset_exploration.ipynb
jupyter nbconvert --to notebook --execute notebooks/02_feature_engineering.ipynb
jupyter nbconvert --to notebook --execute notebooks/03_model_training.ipynb
jupyter nbconvert --to notebook --execute notebooks/04_model_evaluation.ipynb
jupyter nbconvert --to notebook --execute notebooks/05_production_integration.ipynb
```

---

## 📊 Notebook Details

### Notebook 01: Dataset Exploration

**Duration:** ~5-10 minutes

**What it does:**
- Loads CI/CD log dataset
- Visualizes error category distribution
- Creates train/val/test splits (70/15/15)
- Analyzes log statistics

**Outputs:**
- `data/synthetic_logs/train.csv`
- `data/synthetic_logs/val.csv`
- `data/synthetic_logs/test.csv`

**Key Metrics to Check:**
- Total logs: Should be >100
- Class balance ratio: >0.5 (moderate) or >0.7 (good)
- All platforms represented

---

### Notebook 02: Feature Engineering

**Duration:** ~10-20 minutes

**What it does:**
- Extracts TF-IDF features (500 dimensions)
- Extracts structural features (13 dimensions)
- Extracts platform features (3 dimensions)
- Combines all features into matrices
- Saves features and preprocessors

**Outputs:**
- `models/X_train.pkl`, `X_val.pkl`, `X_test.pkl`
- `models/y_train.pkl`, `y_val.pkl`, `y_test.pkl`
- `models/tfidf_vectorizer.pkl`
- `models/label_encoder.pkl`
- `models/feature_info.pkl`

**Key Metrics to Check:**
- Feature matrix shape: (~70-100, ~516)
- No empty log contents
- All platforms properly encoded

---

### Notebook 03: Model Training

**Duration:** ~5-15 minutes (depends on dataset size)

**What it does:**
- Trains Logistic Regression (baseline)
- Trains Random Forest (100 trees)
- Trains XGBoost (best model)
- Compares models
- Saves all trained models

**Outputs:**
- `models/error_classifier_lr.pkl`
- `models/error_classifier_rf.pkl`
- `models/error_classifier_xgb.pkl` ⭐ Best
- `models/model_metadata.pkl`

**Target Metrics:**
- Validation Accuracy: >70%
- Test Accuracy: >70%
- F1-Score: >0.70
- Inference Time: <100ms

**If accuracy is low (<60%):**
- Check dataset quality
- Ensure balanced classes
- Consider collecting more data
- Try hyperparameter tuning

---

### Notebook 04: Model Evaluation

**Duration:** ~5-10 minutes

**What it does:**
- Comprehensive metrics analysis
- Per-class performance breakdown
- Confusion matrix analysis
- Feature importance analysis
- Confidence calibration
- Production readiness assessment

**Outputs:**
- Visualizations (confusion matrix, metrics charts)
- Performance reports
- Recommendations

**Key Checks:**
- Overall accuracy >75%
- All classes have F1 >0.60
- Low confidence cases <20%
- Average confidence >0.75

---

### Notebook 05: Production Integration

**Duration:** ~5-10 minutes

**What it does:**
- Creates production-ready feature extractor
- Creates ML predictor class
- Tests inference speed
- Exports code to `src/ml/`
- Creates integration guide

**Outputs:**
- `src/ml/feature_extractor.py`
- `src/ml/predictor.py`
- `src/ml/__init__.py`
- `docs/ML_INTEGRATION.md`
- `models/production_metadata.json`

**Key Checks:**
- Inference time <100ms
- All files created successfully
- No import errors in generated code

---

## ✅ Validation Checklist

After running all notebooks, verify:

### Files Created:

```bash
# Check models directory
ls -la models/

# Should contain:
# ✅ X_train.pkl, X_val.pkl, X_test.pkl
# ✅ y_train.pkl, y_val.pkl, y_test.pkl
# ✅ tfidf_vectorizer.pkl
# ✅ label_encoder.pkl
# ✅ feature_info.pkl
# ✅ error_classifier_lr.pkl
# ✅ error_classifier_rf.pkl
# ✅ error_classifier_xgb.pkl
# ✅ model_metadata.pkl
# ✅ production_metadata.json
```

```bash
# Check src/ml directory
ls -la src/ml/

# Should contain:
# ✅ __init__.py
# ✅ feature_extractor.py
# ✅ predictor.py
```

### Quick Test:

```python
# Test if models work
import joblib
from src.ml import ErrorClassifier

# Load classifier
classifier = ErrorClassifier(model_dir='models')

# Test prediction
sample_log = """
[2024-01-15 10:30:45] ERROR: npm install failed
npm ERR! 404 Not Found - GET https://registry.npmjs.org/unknown-package
"""

result = classifier.predict(sample_log, platform='github-actions')
print(f"Predicted: {result.error_type}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Inference time: {result.inference_time_ms:.2f}ms")
```

**Expected Output:**
```
Predicted: dependency_error
Confidence: 85.3%
Inference time: 45.23ms
```

---

## 🐛 Troubleshooting

### Issue 1: "Dataset not found"

**Solution:**
```bash
# Check you're in project root
pwd  # Should be .../ai-logguard

# Check dataset exists
ls data/synthetic_logs/dataset.csv
```

### Issue 2: "Module 'src.ml' not found"

**Solution:**
```bash
# Ensure you've run notebook 05
# Or manually create src/ml/__init__.py

# Make sure src/ is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 3: "Out of memory" during training

**Solution:**
- Reduce `max_features` in TF-IDF (500 → 300)
- Use smaller dataset subset
- Close other applications
- Reduce `n_estimators` in Random Forest (100 → 50)

### Issue 4: Low accuracy (<60%)

**Possible causes:**
- Insufficient training data
- Imbalanced classes (check notebook 01)
- Poor feature extraction (check notebook 02)

**Solutions:**
- Collect more diverse logs
- Ensure `class_weight='balanced'` is used
- Try different `max_features` in TF-IDF
- Add more structural features

### Issue 5: "Kernel died" in Jupyter

**Causes:**
- Out of memory
- Python environment issues

**Solutions:**
```bash
# Restart Jupyter
jupyter notebook

# Or use fresh kernel
# Kernel → Restart & Run All
```

### Issue 6: Slow inference (>500ms)

**Causes:**
- Large models
- Too many features
- Inefficient feature extraction

**Solutions:**
- Use XGBoost (fastest)
- Reduce TF-IDF features (500 → 300)
- Profile code to find bottleneck

---

## 📈 Expected Results

### Dataset Statistics:
- **Total logs:** 100-300
- **Classes:** 5-10 error categories
- **Platforms:** 3 (Jenkins, GitHub Actions, GitLab CI)
- **Train/Val/Test:** 70% / 15% / 15%

### Model Performance:
- **Logistic Regression:**
  - Accuracy: 65-75%
  - F1-Score: 0.63-0.73
  - Inference: 10-30ms

- **Random Forest:**
  - Accuracy: 75-85%
  - F1-Score: 0.73-0.83
  - Inference: 30-80ms

- **XGBoost:** ⭐ Best
  - Accuracy: 78-88%
  - F1-Score: 0.76-0.86
  - Inference: 40-100ms

### Production Readiness:
- ✅ Inference <100ms: PASS
- ✅ Accuracy >70%: PASS
- ✅ F1-Score >0.70: PASS
- ✅ Code exported: PASS

---

## 🎯 Next Steps After Phase 3

Once all notebooks complete successfully:

### 1. Integrate with CLI

```bash
# Update src/cli.py to use ML classifier
# Add --ml flag to analyze command

ai-logguard analyze sample.log --ml
```

### 2. Test End-to-End

```bash
# Test with real logs
ai-logguard analyze tests/sample_logs.txt --ml --llm
```

### 3. Setup Feedback Loop (Phase 4)

- Collect user feedback on predictions
- Create retraining pipeline
- Implement continuous learning

### 4. Deployment

- Package for PyPI
- Create Docker image
- Write deployment docs

---

## 📚 Additional Resources

### Documentation:
- [NOTEBOOK_VALIDATION.md](NOTEBOOK_VALIDATION.md) - Detailed validation report
- [ML_INTEGRATION.md](ML_INTEGRATION.md) - How to integrate ML into CLI
- [ROADMAP.md](../ROADMAP.md) - Overall project roadmap

### Scripts:
- `scripts/fix_notebooks.py` - Automatic notebook fixes
- `scripts/retrain.py` - Model retraining (Phase 4)

### Testing:
```bash
# Run unit tests
pytest tests/test_ml.py

# Test notebooks
pytest --nbmval notebooks/
```

---

## 💡 Tips & Best Practices

### 1. Iterative Development:
- Run notebooks one at a time
- Verify output before proceeding
- Save checkpoints frequently

### 2. Experiment Tracking:
- Keep notes on hyperparameters
- Track model versions
- Document performance changes

### 3. Data Quality:
- More diverse logs = better model
- Balance classes when possible
- Regular dataset updates

### 4. Performance Monitoring:
- Track inference time
- Monitor accuracy over time
- Watch for model drift

### 5. Code Quality:
- Type hints in production code
- Comprehensive error handling
- Unit tests for all modules

---

## ❓ FAQs

**Q: How long does Phase 3 take to complete?**
A: 30-60 minutes total if running sequentially. Can be faster with GPU.

**Q: Can I run notebooks in parallel?**
A: No, they must run sequentially (01 → 02 → 03 → 04 → 05).

**Q: Do I need GPU?**
A: No, CPU is sufficient. Models train in <5 minutes on CPU.

**Q: Can I skip notebook 04?**
A: Not recommended, but notebook 05 can still run without it.

**Q: What if I want to retrain?**
A: Just re-run notebooks 02 → 03 with new data. Notebooks 04-05 will pick up new models.

**Q: How do I update the model?**
A: Re-run notebook 03 to train new models. They'll automatically save to `models/`.

---

## 🎉 Success Criteria

Phase 3 is complete when:

- ✅ All 5 notebooks execute without errors
- ✅ Test accuracy >70%
- ✅ All model files created in `models/`
- ✅ Production code exported to `src/ml/`
- ✅ Quick test passes (classifier works)
- ✅ Documentation updated

**Congratulations! You're ready for Phase 4: Feedback Loop & Continuous Learning** 🚀

---

**Last Updated:** 2024-01-30
**Author:** AI LogGuard Team
**Version:** 1.0.0
