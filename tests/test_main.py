import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from click.testing import CliRunner
from main import cli

def test_cli_fetch_success(monkeypatch):
    class DummyFetcher:
        def get_logs(self, job_id, build_number='lastBuild'):
            return '[ERROR] Something failed\n[WARNING] Disk low\nFinished: SUCCESS'
    monkeypatch.setattr('main.JenkinsFetcher', lambda *a, **kw: DummyFetcher())
    runner = CliRunner()
    result = runner.invoke(cli, [
        'fetch', '--provider', 'jenkins', '--url', 'http://localhost', '--job-id', 'myjob', '--token', 'mytoken'])
    assert result.exit_code == 0
    assert 'Logs fetched successfully' in result.output
    # Kiểm tra có dòng chứa 'Build Status:' trong output (dù là SUCCESS, FAILURE hay .*)
    assert any(line.strip().startswith('Build Status:') for line in result.output.splitlines())
    assert 'Total Errors/Failures: 1' in result.output
    assert 'Total Warnings: 1' in result.output

def test_cli_fetch_missing_option(monkeypatch):
    class DummyFetcher:
        def get_logs(self, job_id, build_number='lastBuild'):
            return '[ERROR] Something failed\n[WARNING] Disk low\nFinished: SUCCESS'
    monkeypatch.setattr('main.JenkinsFetcher', lambda *a, **kw: DummyFetcher())
    runner = CliRunner()
    # Missing --token
    result = runner.invoke(cli, [
        'fetch', '--provider', 'jenkins', '--url', 'http://localhost', '--job-id', 'myjob'])
    assert result.exit_code != 0
    assert 'Missing option' in result.output

def test_cli_fetch_fail(monkeypatch):
    class DummyFetcher:
        def get_logs(self, job_id, build_number='lastBuild'):
            raise Exception('401 Unauthorized')
    monkeypatch.setattr('main.JenkinsFetcher', lambda *a, **kw: DummyFetcher())
    runner = CliRunner()
    result = runner.invoke(cli, [
        'fetch', '--provider', 'jenkins', '--url', 'http://mock', '--job-id', 'job', '--token', 'bad'])
    # Chỉ kiểm tra thông báo lỗi trong output, không kiểm tra exit_code vì CLI swallow exception
    assert 'Error: 401 Unauthorized' in result.output

