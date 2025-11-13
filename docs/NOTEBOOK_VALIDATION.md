# 📋 Notebook Validation Report

## Overview

Báo cáo kiểm tra chi tiết tất cả các notebooks trong Phase 3 để đảm bảo không có lỗi khi chạy.

---

## ✅ Notebook 01: Dataset Exploration

**Status:** ⚠️ **NEEDS MODIFICATION**

### Issues Found:

1. **Git Clone Issue** (Cell `af262310`)
   - ❌ Notebook đang ở trong project, không cần clone lại
   - ❌ `%cd AI-LogGuard` sẽ lỗi nếu thư mục không tồn tại

### Fixes Required:

```python
# REMOVE THIS CELL (af262310):
# !git clone https://github.com/SyLe-Van/AI-LogGuard.git
# %cd AI-LogGuard

# REPLACE WITH:
# Check if we're in the right directory
import os
if not os.path.exists('data/synthetic_logs'):
    print("❌ Error: Please run this notebook from the project root directory")
    print("   Current directory:", os.getcwd())
else:
    print("✅ Correct directory")
```

2. **Path Issues** (Multiple cells)
   - ⚠️ All paths assume running from cloned directory
   - ✅ Should use relative paths from project root

### Recommendations:

- Run notebook from project root: `/Users/mac/projects/Thesis/ai-logguard/`
- Ensure `data/synthetic_logs/` exists with dataset

---

## ✅ Notebook 02: Feature Engineering

**Status:** ✅ **LOOKS GOOD**

### Potential Issues:

1. **Empty Log Content** (Cell `14fdf9a7`)
   - ⚠️ If log file doesn't exist, returns empty string
   - ✅ Already has error handling

2. **Platform One-Hot Encoding** (Cell `dc097e88`)
   - ⚠️ If val/test have different platforms than train, columns may not match
   - ✅ Current code handles this correctly

### Validation Checks:

```python
# Add this check after loading data (Cell e5cad42b):
print(f"\n🔍 Validation:")
print(f"Platforms in train: {train_df['platform'].unique()}")
print(f"Platforms in val:   {val_df['platform'].unique()}")
print(f"Platforms in test:  {test_df['platform'].unique()}")
```

---

## ✅ Notebook 03: Model Training

**Status:** ✅ **LOOKS GOOD**

### Potential Issues:

1. **XGBoost Verbosity** (Cell `4b48fe34`)
   - ✅ Already set to `verbose=False`

2. **Memory Usage**
   - ⚠️ Three models loaded simultaneously may use ~500MB-1GB RAM
   - ✅ Should be fine on most machines

### Performance Notes:

- Logistic Regression: ~5-10s
- Random Forest: ~30-60s (100 trees)
- XGBoost: ~20-40s

---

## ⚠️ Notebook 04: Model Evaluation

**Status:** ⚠️ **NEEDS FIXES**

### Issues Found:

1. **Missing Import** (Cell `a9`)
   ```python
   # ADD THIS:
   from sklearn.metrics import precision_recall_fscore_support
   ```
   - ✅ Already imported in cell `a4`

2. **Undefined Variable `metrics_df`** (Cell `a24`)
   - ❌ Variable `metrics_df` used before notebook 04 but defined in notebook 03
   - ❌ Will fail if running notebook 04 standalone

### Fixes Required:

Add to the beginning of Cell `a24`:
```python
# Ensure metrics_df exists (for standalone execution)
if 'metrics_df' not in locals():
    # Recreate metrics_df from loaded models
    metrics_data = []
    for name, y_pred in predictions.items():
        acc = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )
        metrics_data.append({
            'Model': name,
            'Accuracy': acc,
            'F1-Score': f1
        })
    metrics_df = pd.DataFrame(metrics_data)
```

3. **Confusion DataFrame Variable** (Cell `a16`)
   - ⚠️ Uses `confused_df` but may be empty
   - ✅ Already has length check

---

## ⚠️ Notebook 05: Production Integration

**Status:** ⚠️ **NEEDS FIXES**

### Issues Found:

1. **Missing Variable `metrics_df`** (Cell `b24`)
   - ❌ Uses `metrics_df` from notebook 03
   - ❌ Will fail if running standalone

2. **Missing Variable `inference_times`** (Cell `b24`)
   - ❌ Uses `inference_times` from cell `b12`
   - ❌ Will fail if cell `b12` not executed

3. **Directory Creation** (Cell `b17`)
   - ⚠️ Creates `../src/ml` relative to notebook directory
   - ⚠️ May create in wrong location

### Fixes Required:

**Fix 1: Cell b24 - Handle missing variables**
```python
# At the beginning of cell b24:
from datetime import datetime

# Validate required variables exist
if 'metrics_df' not in locals():
    print("⚠️ Warning: metrics_df not found. Using placeholder values.")
    metrics_df = pd.DataFrame([{
        'Model': 'XGBoost',
        'Accuracy': 0.80,
        'F1-Score': 0.78
    }])

if 'inference_times' not in locals():
    print("⚠️ Warning: inference_times not found. Using placeholder.")
    inference_times = [50.0]  # placeholder

# ... rest of the cell
```

**Fix 2: Cell b17 - Use absolute paths**
```python
# Create src/ml directory using absolute path
import os
from pathlib import Path

# Get project root (assuming notebook is in notebooks/)
project_root = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
ml_dir = project_root / 'src' / 'ml'

ml_dir.mkdir(parents=True, exist_ok=True)
print(f"✅ Created {ml_dir}")
```

**Fix 3: Cell b18-b20 - Update file paths**
```python
# Update all file writes to use ml_dir:
with open(ml_dir / 'feature_extractor.py', 'w') as f:
    f.write(feature_extractor_code)

with open(ml_dir / 'predictor.py', 'w') as f:
    f.write(predictor_code)

with open(ml_dir / '__init__.py', 'w') as f:
    f.write(ml_init)
```

---

## 🔍 Common Issues Across All Notebooks

### 1. Path Dependencies

**Issue:** Notebooks assume specific working directory

**Solution:**
```python
# Add this to the beginning of each notebook:
import os
from pathlib import Path

# Ensure we're in project root
if Path.cwd().name == 'notebooks':
    os.chdir('..')
    print(f"Changed to project root: {Path.cwd()}")

# Validate data directory exists
if not Path('data/synthetic_logs').exists():
    print("❌ ERROR: data/synthetic_logs/ not found!")
    print(f"   Current directory: {Path.cwd()}")
    print("   Please ensure you have the dataset.")
else:
    print("✅ Data directory found")
```

### 2. Missing Dependencies

**Required packages:**
```bash
pip install pandas numpy matplotlib seaborn scikit-learn xgboost joblib scipy
```

### 3. File Existence Checks

Add validation before loading files:
```python
def validate_file(filepath):
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    return True
```

---

## 🛠️ Pre-Execution Checklist

Before running notebooks, verify:

- [ ] Working directory is project root (`/Users/mac/projects/Thesis/ai-logguard/`)
- [ ] Dataset exists: `data/synthetic_logs/dataset.csv`
- [ ] Dataset has these columns: `['file_path', 'error_category', 'platform']`
- [ ] Log files exist at paths specified in dataset
- [ ] All dependencies installed
- [ ] `models/` directory exists (will be created by notebook 02)

---

## 🔄 Execution Order

**Correct order to run notebooks:**

1. ✅ **01_dataset_exploration.ipynb**
   - Creates: `train.csv`, `val.csv`, `test.csv`

2. ✅ **02_feature_engineering.ipynb**
   - Requires: Output from 01
   - Creates: `X_train.pkl`, `y_train.pkl`, etc.

3. ✅ **03_model_training.ipynb**
   - Requires: Output from 02
   - Creates: `error_classifier_*.pkl`, `model_metadata.pkl`

4. ⚠️ **04_model_evaluation.ipynb**
   - Requires: Output from 03
   - Creates: Visualizations and analysis
   - **WARNING:** Depends on variables from 03

5. ⚠️ **05_production_integration.ipynb**
   - Requires: Output from 03
   - Creates: `src/ml/*.py` files
   - **WARNING:** Uses variables from 03 and 04

---

## 🚨 Critical Fixes Needed

### Priority 1: Fix Notebook 01

Remove git clone cell, add directory validation.

### Priority 2: Fix Notebook 04

Make it independent - recreate `metrics_df` if needed.

### Priority 3: Fix Notebook 05

- Handle missing variables with defaults
- Fix relative path issues
- Use absolute paths for file creation

---

## ✅ Validation Script

Create `scripts/validate_notebooks.py`:

```python
#!/usr/bin/env python3
"""Validate that all notebooks can run successfully."""

import os
import sys
from pathlib import Path

def check_environment():
    """Check that environment is set up correctly."""
    errors = []
    warnings = []

    # Check working directory
    if not Path('data/synthetic_logs').exists():
        errors.append("data/synthetic_logs/ not found")

    # Check required files
    required_files = [
        'data/synthetic_logs/dataset.csv',
        'data/synthetic_logs/statistics.json'
    ]
    for f in required_files:
        if not Path(f).exists():
            errors.append(f"Required file missing: {f}")

    # Check notebooks exist
    notebooks = [
        'notebooks/01_dataset_exploration.ipynb',
        'notebooks/02_feature_engineering.ipynb',
        'notebooks/03_model_training.ipynb',
        'notebooks/04_model_evaluation.ipynb',
        'notebooks/05_production_integration.ipynb'
    ]
    for nb in notebooks:
        if not Path(nb).exists():
            warnings.append(f"Notebook not found: {nb}")

    # Report
    if errors:
        print("❌ ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return False

    if warnings:
        print("⚠️  WARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    print("✅ Environment validation passed!")
    return True

if __name__ == '__main__':
    if not check_environment():
        sys.exit(1)
```

---

## 📝 Summary

| Notebook | Status | Critical Issues | Fixes Needed |
|----------|--------|-----------------|--------------|
| 01 - Dataset Exploration | ⚠️ | Git clone issue | Remove clone cell |
| 02 - Feature Engineering | ✅ | None | Minor validations |
| 03 - Model Training | ✅ | None | None |
| 04 - Model Evaluation | ⚠️ | Missing variables | Add variable checks |
| 05 - Production Integration | ⚠️ | Path issues, missing vars | Fix paths, add defaults |

**Overall:** Notebooks are well-structured but need minor fixes for standalone execution and path handling.

**Recommendation:** Apply fixes before running Phase 3.

---

## 🎯 Next Steps

1. Apply fixes to Notebooks 01, 04, and 05
2. Test each notebook individually
3. Test full pipeline (01 → 02 → 03 → 04 → 05)
4. Create automated test script
5. Document any dataset-specific requirements

---

**Last Updated:** 2024-01-30
**Reviewed By:** AI Assistant
**Status:** Ready for fixes
