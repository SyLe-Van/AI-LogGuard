import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/fetchers')))
from gitlab_fetcher import GitLabFetcher

def test_gitlab_fetcher():
    fetcher = GitLabFetcher('http://localhost', 'token')
    logs = fetcher.get_logs('myjob')
    assert 'Mock GitLab logs' in logs
