import pytest
from src.fetchers import JenkinsFetcher, GitLabFetcher

def test_jenkins_fetcher():
    fetcher = JenkinsFetcher()
    assert hasattr(fetcher, 'fetch')

def test_gitlab_fetcher():
    fetcher = GitLabFetcher()
    assert hasattr(fetcher, 'fetch')
