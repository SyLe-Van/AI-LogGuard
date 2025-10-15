
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from parse import basic_parse
import pytest

SAMPLE_LOGS = """
[INFO] Start
[WARNING] Deprecated
[ERROR] Fail due to missing file
FAILED compilation
"""

def test_basic_parse_counts():
    summary = basic_parse(SAMPLE_LOGS)
    assert "Total Errors/Failures: 2" in summary  # [ERROR] và FAILED
    assert "Total Warnings: 1" in summary  # [WARNING]

def test_basic_parse_top_errors():
    summary = basic_parse(SAMPLE_LOGS)
    assert "[ERROR] Fail due to missing file" in summary
    assert "FAILED compilation" in summary
    assert "Top Errors/Failures:" in summary  # Có top list

def test_basic_parse_empty_logs():
    summary = basic_parse("")
    assert "No errors found." in summary  # Handle empty

# Edge case: chỉ warning, không error
def test_only_warnings():
    logs = """
    [WARNING] Disk almost full
    warning: deprecated API
    [Pipeline] echo
    === Stage: Build ===
    """
    summary = basic_parse(logs)
    assert "Total Errors/Failures: 0" in summary
    assert "Total Warnings: 2" in summary
    assert "Top Warnings:" in summary

# Edge case: nhiều dòng trùng lặp error/warning
def test_duplicate_errors_warnings():
    logs = """
    [ERROR] Something failed
    [ERROR] Something failed
    [WARNING] Disk low
    [WARNING] Disk low
    """
    summary = basic_parse(logs)
    assert "Total Errors/Failures: 1" in summary
    assert "Total Warnings: 1" in summary

# Edge case: lỗi/cảnh báo ở nhiều stage
def test_errors_warnings_multiple_stages():
    logs = """
    [Pipeline] { (Build)
    [ERROR] Build failed
    [Pipeline] { (Test)
    [WARNING] Test slow
    [Pipeline] { (Deploy)
    FAILED deployment
    """
    summary = basic_parse(logs)
    assert "[Stage: Build] [ERROR] Build failed" in summary
    assert "[Stage: Deploy] FAILED deployment" in summary
    assert "[Stage: Test] [WARNING] Test slow" in summary

# Edge case: biến thể error/warning
def test_error_warning_variants():
    logs = """
    error: file not found
    fail: could not connect
    exception: NullPointer
    ERR: short error
    WARNING: risky
    """
    summary = basic_parse(logs)
    assert "error: file not found" in summary
    assert "fail: could not connect" in summary
    assert "exception: NullPointer" in summary
    assert "ERR: short error" in summary
    assert "WARNING: risky" in summary

# Edge case: lỗi/cảnh báo nằm trong dòng script
def test_script_lines_ignored():
    logs = """
    + echo [ERROR] Not real error
    + echo WARNING: Not real warning
    [ERROR] Real error
    WARNING: Real warning
    """
    summary = basic_parse(logs)
    assert "Total Errors/Failures: 1" in summary
    assert "Total Warnings: 1" in summary
    assert "[ERROR] Real error" in summary
    assert "WARNING: Real warning" in summary

# Edge case: build status FAILURE
def test_build_status_failure():
    logs = """
    [ERROR] Something failed
    Finished: FAILURE
    """
    summary = basic_parse(logs)
    assert "Build Status: FAILURE" in summary

# Edge case: không có trạng thái build
def test_no_build_status():
    logs = """
    [ERROR] Something failed
    """
    summary = basic_parse(logs)
    assert "Build Status: UNKNOWN" in summary

# Edge case: logs rất lớn
def test_large_logs():
    logs = "[ERROR] fail\n" * 10000 + "[WARNING] warn\n" * 10000 + "Finished: SUCCESS"
    summary = basic_parse(logs)
    assert "Build Status: SUCCESS" in summary
    assert "Total Errors/Failures: 1" in summary
    assert "Total Warnings: 1" in summary
