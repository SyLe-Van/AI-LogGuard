class GitLabFetcher:
    def __init__(self, url, token, username='gitlab'):
        self.url = url.rstrip('/')
        self.token = token
        self.username = username

    def get_logs(self, job_id):
        # Placeholder: trả về mock logs
        return "Mock GitLab logs\n[ERROR] Dependency conflict\n[INFO] Build started"
