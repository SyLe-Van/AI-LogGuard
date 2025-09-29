class JenkinsFetcher:
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def get_logs(self, job_id):
        return "Mock Jenkins logs\n[ERROR] Build failed\n[WARNING] Deprecated API"  # Mock data

class GitLabFetcher:
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def get_logs(self, job_id):
        return "Mock GitLab logs\n[ERROR] Dependency conflict\n[INFO] Build started"  # Mock data
