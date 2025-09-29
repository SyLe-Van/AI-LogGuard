import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from main import JenkinsFetcher, GitLabFetcher

def test_jenkins_fetcher():
    fetcher = JenkinsFetcher('http://localhost', 'token')
    logs = fetcher.get_logs('myjob')
    assert 'Mock Jenkins logs' in logs

def test_gitlab_fetcher():
    fetcher = GitLabFetcher('http://localhost', 'token')
    logs = fetcher.get_logs('myjob')
    assert 'Mock GitLab logs' in logs