# Fix for Notebook 01 - Cell 8c95ecb7 and 7a8e990d

## Problem

File paths in `dataset.csv` are relative (`logs/...`) but need to be prefixed with `data/synthetic_logs/` to work.

## Solution

Replace the two problematic cells with the fixed versions below:

---

## Cell 8c95ecb7 - FIXED VERSION

```python
# Read and display sample logs from each category
def display_sample_log(category, max_lines=30):
    """Display a sample log from a specific error category"""
    sample = df[df['error_category'] == category].iloc[0]

    print("=" * 80)
    print(f"📝 Category: {category}")
    print(f"🔧 Platform: {sample['platform']}")
    print(f"📄 File: {sample['file_path']}")
    print("=" * 80)

    # Construct full path (file_path in CSV is relative to data/synthetic_logs/)
    base_path = Path('data/synthetic_logs')
    log_path = base_path / sample['file_path']

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        print(f"\nTotal lines: {len(lines)}")
        print(f"\nFirst {max_lines} lines:")
        print("-" * 80)
        for i, line in enumerate(lines[:max_lines], 1):
            print(f"{i:3d} | {line}")

        if len(lines) > max_lines:
            print(f"\n... ({len(lines) - max_lines} more lines)")
        print("\n")
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {log_path}")
        print(f"   Please check if log files exist in data/synthetic_logs/")
        print("\n")
    except Exception as e:
        print(f"❌ ERROR reading file: {e}")
        print("\n")

# Display one sample from each category
print("📂 Displaying sample logs from each category...\n")
for category in df['error_category'].unique():
    display_sample_log(category, max_lines=25)
```

---

## Cell 7a8e990d - FIXED VERSION

```python
# Read a few log files to analyze text characteristics
log_lengths = []
base_path = Path('data/synthetic_logs')

print("📂 Reading sample log files...")
for file_path in df['file_path'].head(50):  # Sample 50 logs
    try:
        full_path = base_path / file_path
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            log_lengths.append(len(content))
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        continue
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        continue

if len(log_lengths) == 0:
    print("❌ ERROR: No log files could be read!")
    print("   Please check if log files exist in data/synthetic_logs/logs/")
else:
    print(f"\n📏 Log File Statistics (sample of {len(log_lengths)} logs):")
    print(f"Average length: {np.mean(log_lengths):.0f} characters")
    print(f"Min length: {np.min(log_lengths)} characters")
    print(f"Max length: {np.max(log_lengths)} characters")
    print(f"Median length: {np.median(log_lengths):.0f} characters")

    # Visualize log length distribution
    plt.figure(figsize=(10, 5))
    plt.hist(log_lengths, bins=20, color='skyblue', edgecolor='black')
    plt.xlabel('Log Length (characters)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Log File Lengths', fontsize=14, fontweight='bold')
    plt.axvline(np.mean(log_lengths), color='red', linestyle='--',
                label=f'Mean: {np.mean(log_lengths):.0f}')
    plt.legend()
    plt.tight_layout()
    plt.show()
```

---

## Key Changes

1. **Added base path construction:**
   ```python
   base_path = Path('data/synthetic_logs')
   log_path = base_path / sample['file_path']
   ```

2. **Added error handling:**
   - Try-except blocks for FileNotFoundError
   - Graceful handling of missing files
   - Clear error messages

3. **Added encoding specification:**
   ```python
   with open(log_path, 'r', encoding='utf-8') as f:
   ```

4. **Added validation:**
   - Check if any files were successfully read
   - Skip files that can't be read instead of crashing

---

## How to Apply

### Option 1: Manual (in Jupyter)

1. Open notebook `01_dataset_exploration.ipynb`
2. Find cell with id `8c95ecb7` (Section 5)
3. Replace entire cell content with "Cell 8c95ecb7 - FIXED VERSION" above
4. Find cell with id `7a8e990d` (Section 7)
5. Replace entire cell content with "Cell 7a8e990d - FIXED VERSION" above
6. Re-run the cells

### Option 2: Automatic (run updated fix script)

The fix script will be updated to handle this automatically.

---

## Testing

After applying the fix, you should see:

```
📂 Displaying sample logs from each category...

================================================================================
📝 Category: dependency_error
🔧 Platform: github-actions
📄 File: logs/github-actions_dependency_error_10.txt
================================================================================

Total lines: 15

First 25 lines:
--------------------------------------------------------------------------------
  1 | [2024-01-15T10:30:21.123Z] Starting build #10
  2 | [2024-01-15T10:30:21.456Z] Checking out code...
  ...
```

If you still see errors, verify:

```bash
# Check dataset structure
head -3 data/synthetic_logs/dataset.csv

# Check if log files exist
ls data/synthetic_logs/logs/ | head -5

# Verify a specific file
cat data/synthetic_logs/logs/github-actions_dependency_error_10.txt
```
