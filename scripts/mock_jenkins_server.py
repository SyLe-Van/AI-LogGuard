#!/usr/bin/env python3
"""
Mock Jenkins server để test fetch + analyze
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import base64
import threading
import time

# Sample log content
SAMPLE_LOG = """[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/test-job
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Build)
[Pipeline] sh
+ npm install
npm WARN deprecated package@1.0.0
[Pipeline] sh
+ npm run build
[ERROR] Build failed: Missing environment variable DATABASE_URL
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
ERROR: script returned exit code 1
Finished: FAILURE
"""

class MockJenkinsHandler(BaseHTTPRequestHandler):
    """
    Mock Jenkins API handler
    """
    
    def do_GET(self):
        # Check authorization
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return
        
        # Validate token (optional)
        try:
            encoded = auth_header.split(' ')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')
            # Expected: admin:test_token
        except:
            self.send_response(401)
            self.end_headers()
            return
        
        # Handle console text request
        if '/consoleText' in self.path:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(SAMPLE_LOG.encode('utf-8'))
            print(f"✅ Served console log for {self.path}")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_mock_server(port=9999):
    """
    Start mock Jenkins server in background
    """
    server = HTTPServer(('localhost', port), MockJenkinsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"🚀 Mock Jenkins server started on http://localhost:{port}")
    return server

if __name__ == "__main__":
    print("=" * 70)
    print("Mock Jenkins Server for Testing")
    print("=" * 70)
    
    server = start_mock_server(port=9999)
    
    print("\n📝 Test commands:")
    print("\n1. Fetch only:")
    print("   ailog fetch -p jenkins -u http://localhost:9999 \\")
    print("     -j test-project -t test_token")
    
    print("\n2. Fetch + Save:")
    print("   ailog fetch -p jenkins -u http://localhost:9999 \\")
    print("     -j test-project -t test_token -s /tmp/test.log")
    
    print("\n3. Fetch + Analyze (NEW!):")
    print("   ailog fetch -p jenkins -u http://localhost:9999 \\")
    print("     -j test-project -t test_token -a")
    
    print("\n4. Fetch + Analyze + Save:")
    print("   ailog fetch -p jenkins -u http://localhost:9999 \\")
    print("     -j test-project -t test_token -a -s /tmp/analyzed.log")
    
    print("\n" + "=" * 70)
    print("Server running... Press Ctrl+C to stop")
    print("=" * 70)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server...")
        server.shutdown()
