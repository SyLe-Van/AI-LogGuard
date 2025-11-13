#!/usr/bin/env python3
"""
Fix notebook 01 - Path issues with log files.
This script fixes cells that try to read log files with incorrect paths.
"""

import json
from pathlib import Path
import sys


def fix_notebook_01():
    """Fix path issues in notebook 01."""
    nb_path = Path('notebooks/01_dataset_exploration.ipynb')

    if not nb_path.exists():
        print(f"❌ {nb_path} not found")
        print(f"   Current directory: {Path.cwd()}")
        return False

    print(f"📂 Loading notebook: {nb_path}")
    with open(nb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    fixed_count = 0

    # Fix cell 8c95ecb7 - display_sample_log function
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == '8c95ecb7':
            cell['source'] = [
                "# Read and display sample logs from each category\n",
                "def display_sample_log(category, max_lines=30):\n",
                "    \"\"\"Display a sample log from a specific error category\"\"\"\n",
                "    sample = df[df['error_category'] == category].iloc[0]\n",
                "    \n",
                "    print(\"=\" * 80)\n",
                "    print(f\"📝 Category: {category}\")\n",
                "    print(f\"🔧 Platform: {sample['platform']}\")\n",
                "    print(f\"📄 File: {sample['file_path']}\")\n",
                "    print(\"=\" * 80)\n",
                "    \n",
                "    # Construct full path (file_path in CSV is relative to data/synthetic_logs/)\n",
                "    base_path = Path('data/synthetic_logs')\n",
                "    log_path = base_path / sample['file_path']\n",
                "    \n",
                "    try:\n",
                "        with open(log_path, 'r', encoding='utf-8') as f:\n",
                "            content = f.read()\n",
                "        \n",
                "        lines = content.split('\\n')\n",
                "        print(f\"\\nTotal lines: {len(lines)}\")\n",
                "        print(f\"\\nFirst {max_lines} lines:\")\n",
                "        print(\"-\" * 80)\n",
                "        for i, line in enumerate(lines[:max_lines], 1):\n",
                "            print(f\"{i:3d} | {line}\")\n",
                "        \n",
                "        if len(lines) > max_lines:\n",
                "            print(f\"\\n... ({len(lines) - max_lines} more lines)\")\n",
                "        print(\"\\n\")\n",
                "    except FileNotFoundError:\n",
                "        print(f\"❌ ERROR: File not found: {log_path}\")\n",
                "        print(f\"   Please check if log files exist in data/synthetic_logs/\")\n",
                "        print(\"\\n\")\n",
                "    except Exception as e:\n",
                "        print(f\"❌ ERROR reading file: {e}\")\n",
                "        print(\"\\n\")\n",
                "\n",
                "# Display one sample from each category\n",
                "print(\"📂 Displaying sample logs from each category...\\n\")\n",
                "for category in df['error_category'].unique():\n",
                "    display_sample_log(category, max_lines=25)"
            ]
            fixed_count += 1
            print("✅ Fixed cell 8c95ecb7 (display_sample_log)")
            break

    # Fix cell 7a8e990d - log statistics
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == '7a8e990d':
            cell['source'] = [
                "# Read a few log files to analyze text characteristics\n",
                "log_lengths = []\n",
                "base_path = Path('data/synthetic_logs')\n",
                "\n",
                "print(\"📂 Reading sample log files...\")\n",
                "for file_path in df['file_path'].head(50):  # Sample 50 logs\n",
                "    try:\n",
                "        full_path = base_path / file_path\n",
                "        with open(full_path, 'r', encoding='utf-8') as f:\n",
                "            content = f.read()\n",
                "            log_lengths.append(len(content))\n",
                "    except FileNotFoundError:\n",
                "        print(f\"⚠️  File not found: {file_path}\")\n",
                "        continue\n",
                "    except Exception as e:\n",
                "        print(f\"⚠️  Error reading {file_path}: {e}\")\n",
                "        continue\n",
                "\n",
                "if len(log_lengths) == 0:\n",
                "    print(\"❌ ERROR: No log files could be read!\")\n",
                "    print(\"   Please check if log files exist in data/synthetic_logs/logs/\")\n",
                "else:\n",
                "    print(f\"\\n📏 Log File Statistics (sample of {len(log_lengths)} logs):\")\n",
                "    print(f\"Average length: {np.mean(log_lengths):.0f} characters\")\n",
                "    print(f\"Min length: {np.min(log_lengths)} characters\")\n",
                "    print(f\"Max length: {np.max(log_lengths)} characters\")\n",
                "    print(f\"Median length: {np.median(log_lengths):.0f} characters\")\n",
                "\n",
                "    # Visualize log length distribution\n",
                "    plt.figure(figsize=(10, 5))\n",
                "    plt.hist(log_lengths, bins=20, color='skyblue', edgecolor='black')\n",
                "    plt.xlabel('Log Length (characters)')\n",
                "    plt.ylabel('Frequency')\n",
                "    plt.title('Distribution of Log File Lengths', fontsize=14, fontweight='bold')\n",
                "    plt.axvline(np.mean(log_lengths), color='red', linestyle='--',\n",
                "                label=f'Mean: {np.mean(log_lengths):.0f}')\n",
                "    plt.legend()\n",
                "    plt.tight_layout()\n",
                "    plt.show()"
            ]
            fixed_count += 1
            print("✅ Fixed cell 7a8e990d (log_statistics)")
            break

    # Save fixed notebook
    if fixed_count > 0:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)
        print(f"\n✅ Saved fixed notebook: {nb_path}")
        print(f"   Total fixes applied: {fixed_count}")
        return True
    else:
        print("⚠️  No cells were fixed (already fixed or cells not found)")
        return False


def main():
    """Main function."""
    print("=" * 80)
    print("🔧 NOTEBOOK 01 PATH FIX SCRIPT")
    print("=" * 80)
    print("\nThis script fixes path issues in notebook 01.")
    print("Issue: File paths in CSV are relative but code tries to read them directly.")
    print("Fix: Adds 'data/synthetic_logs/' prefix to all file paths.\n")

    # Check current directory
    cwd = Path.cwd()
    print(f"📂 Current directory: {cwd}")

    # Check if we're in the right place
    if not (cwd / 'notebooks').exists() and not (cwd.parent / 'notebooks').exists():
        print("\n❌ ERROR: Cannot find notebooks/ directory")
        print("   Please run this script from the project root")
        sys.exit(1)

    # Check if dataset exists
    data_path = cwd / 'data/synthetic_logs'
    if not data_path.exists():
        print(f"\n⚠️  WARNING: Dataset directory not found: {data_path}")
        print("   The fix will still be applied, but notebook may not run without data")

    print("\nPress Enter to continue, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)

    print("\n" + "=" * 80)
    print("📝 APPLYING FIX")
    print("=" * 80 + "\n")

    success = fix_notebook_01()

    print("\n" + "=" * 80)
    if success:
        print("✅ FIX APPLIED SUCCESSFULLY")
        print("\nYou can now run notebook 01 without path errors.")
        print("The following cells have been fixed:")
        print("  - Cell 8c95ecb7: display_sample_log() function")
        print("  - Cell 7a8e990d: log file statistics")
        print("\nKey changes:")
        print("  ✅ Added 'data/synthetic_logs/' prefix to file paths")
        print("  ✅ Added error handling for missing files")
        print("  ✅ Added UTF-8 encoding for file reads")
    else:
        print("❌ FIX FAILED OR ALREADY APPLIED")
        print("\nIf cells are already fixed, you can ignore this.")
        print("Otherwise, check error messages above.")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
