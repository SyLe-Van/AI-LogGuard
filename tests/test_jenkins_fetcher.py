import sys
import os
import pytest
import requests_mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/fetchers')))
from jenkins_fetcher import JenkinsFetcher

def test_jenkins_fetcher_success():
	with requests_mock.Mocker() as m:
		m.get('http://localhost:8080/job/test-job/lastBuild/consoleText', text='[ERROR] Test error')
		fetcher = JenkinsFetcher('http://localhost:8080', 'fake_token', 'admin')
		logs = fetcher.get_logs('test-job')
		assert '[ERROR] Test error' in logs

def test_jenkins_fetcher_401():
	with requests_mock.Mocker() as m:
		m.get('http://localhost:8080/job/test-job/lastBuild/consoleText', status_code=401)
		fetcher = JenkinsFetcher('http://localhost:8080', 'wrong_token', 'admin')
		with pytest.raises(Exception, match='Failed to fetch Jenkins logs: 401'):
			fetcher.get_logs('test-job')



