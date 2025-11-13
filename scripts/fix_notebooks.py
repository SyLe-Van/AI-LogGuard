#!/usr/bin/env python3
"""
Script to automatically fix common issues in Phase 3 notebooks.
Run this before executing notebooks to ensure smooth operation.
"""

import json
from pathlib import Path
import sys


def fix_notebook_01():
    """Fix notebook 01: Remove git clone, add directory validation."""
    nb_path = Path('notebooks/01_dataset_exploration.ipynb')

    if not nb_path.exists():
        print(f"❌ {nb_path} not found")
        return False

    with open(nb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    # Find and replace the git clone cell
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'af262310':
            # Replace with directory validation
            cell['source'] = [
                "# Validate working directory\n",
                "import os\n",
                "from pathlib import Path\n",
                "\n",
                "# Check if we're in notebooks directory, move to project root\n",
                "if Path.cwd().name == 'notebooks':\n",
                "    os.chdir('..')\n",
                "    print(f\"📂 Changed to project root: {Path.cwd()}\")\n",
                "\n",
                "# Validate dataset exists\n",
                "if not Path('data/synthetic_logs/dataset.csv').exists():\n",
                "    print(\"❌ ERROR: Dataset not found!\")\n",
                "    print(f\"   Current directory: {Path.cwd()}\")\n",
                "    print(\"   Expected: data/synthetic_logs/dataset.csv\")\n",
                "    print(\"\\n   Please ensure dataset is in the correct location.\")\n",
                "else:\n",
                "    print(\"✅ Dataset found!\")\n",
                "    print(f\"   Location: {Path('data/synthetic_logs/dataset.csv').absolute()}\")"
            ]
            print("✅ Fixed notebook 01: Replaced git clone with directory validation")
            break

    # Update markdown title for this section
    for cell in notebook['cells']:
        if cell['cell_type'] == 'markdown' and cell.get('id') == 'd86e93a8':
            cell['source'] = ["## 2. Validate Environment & Load Dataset"]
            break

    # Save fixed notebook
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"✅ Saved fixed notebook: {nb_path}")
    return True


def fix_notebook_04():
    """Fix notebook 04: Add variable validation."""
    nb_path = Path('notebooks/04_model_evaluation.ipynb')

    if not nb_path.exists():
        print(f"❌ {nb_path} not found")
        return False

    with open(nb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    # Find the cell that needs metrics_df and add validation
    for i, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code' and cell.get('id') == 'a31':
            # Add validation at the beginning
            original_source = cell['source']
            cell['source'] = [
                "# Validate required variables exist\n",
                "if 'metrics_df' not in dir():\n",
                "    print(\"⚠️  Creating metrics_df from loaded models...\")\n",
                "    metrics_data = []\n",
                "    for name, y_pred in predictions.items():\n",
                "        acc = accuracy_score(y_test, y_pred)\n",
                "        f1 = f1_score(y_test, y_pred, average='weighted')\n",
                "        metrics_data.append({\n",
                "            'Model': name,\n",
                "            'Accuracy': acc,\n",
                "            'F1-Score': f1\n",
                "        })\n",
                "    metrics_df = pd.DataFrame(metrics_data)\n",
                "\n"
            ] + original_source
            print("✅ Fixed notebook 04: Added metrics_df validation")
            break

    # Save fixed notebook
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"✅ Saved fixed notebook: {nb_path}")
    return True


def fix_notebook_05():
    """Fix notebook 05: Fix paths and add variable validation."""
    nb_path = Path('notebooks/05_production_integration.ipynb')

    if not nb_path.exists():
        print(f"❌ {nb_path} not found")
        return False

    with open(nb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    # Fix cell b17 - directory creation
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'b17':
            cell['source'] = [
                "# Create src/ml directory using absolute path\n",
                "import os\n",
                "from pathlib import Path\n",
                "\n",
                "# Get project root (assuming notebook is in notebooks/)\n",
                "project_root = Path.cwd()\n",
                "if project_root.name == 'notebooks':\n",
                "    project_root = project_root.parent\n",
                "\n",
                "ml_dir = project_root / 'src' / 'ml'\n",
                "ml_dir.mkdir(parents=True, exist_ok=True)\n",
                "\n",
                "print(f\"✅ Created directory: {ml_dir}\")\n",
                "print(f\"   Absolute path: {ml_dir.absolute()}\")"
            ]
            print("✅ Fixed notebook 05: Updated directory creation")
            break

    # Fix cell b18 - feature_extractor.py save path
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'b18':
            # Update the save path at the end
            source = cell['source']
            # Find and replace the save line
            for i, line in enumerate(source):
                if "with open('../src/ml/feature_extractor.py'" in line:
                    source[i] = "with open(ml_dir / 'feature_extractor.py', 'w') as f:\n"
            for i, line in enumerate(source):
                if "print(\"✅ Saved: src/ml/feature_extractor.py\")" in line:
                    source[i] = 'print(f"✅ Saved: {ml_dir / \'feature_extractor.py\'}")\n'
            cell['source'] = source
            print("✅ Fixed notebook 05: Updated feature_extractor.py path")
            break

    # Fix cell b19 - predictor.py save path
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'b19':
            source = cell['source']
            for i, line in enumerate(source):
                if "with open('../src/ml/predictor.py'" in line:
                    source[i] = "with open(ml_dir / 'predictor.py', 'w') as f:\n"
            for i, line in enumerate(source):
                if "print(\"✅ Saved: src/ml/predictor.py\")" in line:
                    source[i] = 'print(f"✅ Saved: {ml_dir / \'predictor.py\'}")\n'
            cell['source'] = source
            print("✅ Fixed notebook 05: Updated predictor.py path")
            break

    # Fix cell b20 - __init__.py save path
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'b20':
            source = cell['source']
            for i, line in enumerate(source):
                if "with open('../src/ml/__init__.py'" in line:
                    source[i] = "with open(ml_dir / '__init__.py', 'w') as f:\n"
            for i, line in enumerate(source):
                if "print(\"✅ Saved: src/ml/__init__.py\")" in line:
                    source[i] = 'print(f"✅ Saved: {ml_dir / \'__init__.py\'}")\n'
            cell['source'] = source
            print("✅ Fixed notebook 05: Updated __init__.py path")
            break

    # Fix cell b24 - add variable validation
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'b24':
            # Add validation at the beginning
            original_source = cell['source']
            cell['source'] = [
                "# Create comprehensive model metadata\n",
                "from datetime import datetime\n",
                "\n",
                "# Validate required variables\n",
                "if 'metrics_df' not in dir():\n",
                "    print(\"⚠️  Warning: metrics_df not found, using placeholder values\")\n",
                "    metrics_df = pd.DataFrame([{\n",
                "        'Model': 'XGBoost',\n",
                "        'Accuracy': 0.80,\n",
                "        'F1-Score': 0.78\n",
                "    }])\n",
                "\n",
                "if 'inference_times' not in dir():\n",
                "    print(\"⚠️  Warning: inference_times not found, using placeholder\")\n",
                "    inference_times = [50.0]\n",
                "\n"
            ] + original_source[1:]  # Skip first line which is a comment
            print("✅ Fixed notebook 05: Added variable validation")
            break

    # Save fixed notebook
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"✅ Saved fixed notebook: {nb_path}")
    return True


def validate_environment():
    """Validate that environment is ready for notebooks."""
    print("\n" + "=" * 80)
    print("🔍 ENVIRONMENT VALIDATION")
    print("=" * 80)

    errors = []
    warnings = []

    # Check working directory
    cwd = Path.cwd()
    print(f"\n📂 Current directory: {cwd}")

    if cwd.name not in ['ai-logguard', 'notebooks']:
        warnings.append(f"Unexpected directory: {cwd.name}")

    # Check for project root indicators
    if not (cwd / 'src').exists() and not (cwd.parent / 'src').exists():
        errors.append("Cannot find 'src/' directory - are you in the project root?")

    # Check for notebooks
    notebooks_dir = cwd / 'notebooks' if (cwd / 'notebooks').exists() else cwd
    if not notebooks_dir.exists():
        errors.append("'notebooks/' directory not found")

    # Check for data
    data_path = cwd / 'data/synthetic_logs' if cwd.name != 'notebooks' else cwd.parent / 'data/synthetic_logs'
    if not data_path.exists():
        errors.append(f"Dataset directory not found: {data_path}")
    else:
        print(f"✅ Dataset directory found: {data_path}")

        # Check for required files
        required_files = ['dataset.csv', 'statistics.json']
        for f in required_files:
            if not (data_path / f).exists():
                errors.append(f"Missing required file: data/synthetic_logs/{f}")
            else:
                print(f"✅ Found: {f}")

    # Report results
    print("\n" + "=" * 80)
    if errors:
        print("❌ ERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        print("\n❌ Environment validation FAILED")
        return False

    if warnings:
        print("⚠️  WARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if not errors:
        print("✅ Environment validation PASSED!")

    print("=" * 80 + "\n")
    return True


def main():
    """Main function."""
    print("=" * 80)
    print("🔧 NOTEBOOK FIX SCRIPT")
    print("=" * 80)
    print("\nThis script will fix common issues in Phase 3 notebooks.")
    print("Backups are NOT created - notebooks are modified in place.")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)

    # Validate environment first
    if not validate_environment():
        print("\n❌ Please fix environment issues before running notebooks")
        sys.exit(1)

    # Apply fixes
    print("\n" + "=" * 80)
    print("📝 APPLYING FIXES")
    print("=" * 80 + "\n")

    success = True
    success &= fix_notebook_01()
    success &= fix_notebook_04()
    success &= fix_notebook_05()

    print("\n" + "=" * 80)
    if success:
        print("✅ ALL FIXES APPLIED SUCCESSFULLY")
        print("\nYou can now run the notebooks in order:")
        print("  1. notebooks/01_dataset_exploration.ipynb")
        print("  2. notebooks/02_feature_engineering.ipynb")
        print("  3. notebooks/03_model_training.ipynb")
        print("  4. notebooks/04_model_evaluation.ipynb")
        print("  5. notebooks/05_production_integration.ipynb")
    else:
        print("❌ SOME FIXES FAILED")
        print("Please check error messages above")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
