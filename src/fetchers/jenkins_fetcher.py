import requests
import base64
import os

class JenkinsFetcher:
    def __init__(self, url, token, username='admin'):
        self.url = url.rstrip('/')
        self.token = os.getenv('JENKINS_TOKEN', token)
        self.username = username
        auth_str = f"{self.username}:{self.token}"
        self.auth_header = 'Basic ' + base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')

    def get_logs(self, job_id, build_number='lastBuild'):
        endpoint = f"{self.url}/job/{job_id}/{build_number}/consoleText"
        headers = {'Authorization': self.auth_header}
        response = requests.get(endpoint, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch Jenkins logs: {response.status_code} - {response.text}")
        return response.text
