import pytest
from click.testing import CliRunner
from src.main import cli

def test_fetch_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['fetch', '--provider', 'jenkins', '--url', 'http://localhost', '--job-id', 'myjob', '--token', 'mytoken'])
    assert result.exit_code == 0
    assert 'Fetching logs from jenkins' in result.output
    assert 'Mock Jenkins logs' in result.output

def test_missing_option():
    runner = CliRunner()
    result = runner.invoke(cli, ['fetch', '--provider', 'jenkins', '--url', 'http://localhost'])
    assert result.exit_code != 0
    assert 'Missing option' in result.output
