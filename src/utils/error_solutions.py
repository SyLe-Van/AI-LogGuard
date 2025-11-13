"""
Error Solutions Database
Maps specific errors to concrete, actionable fixes
"""

from typing import Dict, List, Optional
import re


class ErrorSolution:
    """Concrete solution for a specific error pattern"""
    
    def __init__(
        self, 
        pattern: str, 
        name: str, 
        causes: List[str], 
        solutions: List[str], 
        priority: int = 5,
        related_patterns: List[str] = None  # ✅ NEW: Related error patterns (same root cause)
    ):
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.name = name
        self.causes = causes
        self.solutions = solutions
        self.priority = priority  # Lower = higher priority
        self.related_patterns = related_patterns or []  # ✅ Patterns that indicate same root cause
    
    def matches(self, log_content: str) -> bool:
        """Check if this solution applies to the log"""
        return bool(self.pattern.search(log_content))
    
    def get_related_errors(self, log_content: str) -> List[str]:
        """Find related errors in log (same root cause, different symptoms)"""
        related = []
        for related_pattern in self.related_patterns:
            match = re.search(related_pattern, log_content, re.IGNORECASE)
            if match:
                related.append(match.group(0))
        return related


# ✅ CONCRETE SOLUTIONS DATABASE
ERROR_SOLUTIONS = [
    # === DOCKER ERRORS ===
    ErrorSolution(
        pattern=r'docker: not found|docker: command not found',
        name='Docker Not Installed',
        causes=[
            'Docker is not installed on Jenkins agent',
            'Docker not in PATH environment variable',
            'Jenkins user does not have Docker permissions',
        ],
        solutions=[
            '1. Install Docker on Jenkins agent:\n'
            '   ```bash\n'
            '   sudo apt-get update && sudo apt-get install docker.io\n'
            '   # OR for RHEL/CentOS:\n'
            '   sudo yum install docker\n'
            '   ```',
            
            '2. Add jenkins user to docker group:\n'
            '   ```bash\n'
            '   sudo usermod -aG docker jenkins\n'
            '   sudo systemctl restart jenkins\n'
            '   ```',
            
            '3. Verify Docker is in PATH:\n'
            '   ```bash\n'
            '   which docker  # Should print /usr/bin/docker\n'
            '   echo $PATH    # Should include /usr/bin\n'
            '   ```',
        ],
        priority=1,
        related_patterns=[
            r'exit code 127',  # ✅ Related: command not found exit code
            r'command not found',  # ✅ Related: generic command not found
            r'/bin/sh.*docker.*not found',  # ✅ Related: shell error
        ],
    ),
    
    ErrorSolution(
        pattern=r'permission denied.*docker\.sock|cannot connect to the docker daemon',
        name='Docker Permission Denied',
        causes=[
            'Jenkins user not in docker group',
            'Docker socket permissions are too restrictive',
            'Docker daemon not running',
        ],
        solutions=[
            '1. Add jenkins to docker group (most common fix):\n'
            '   ```bash\n'
            '   sudo usermod -aG docker jenkins\n'
            '   sudo systemctl restart jenkins\n'
            '   ```',
            
            '2. Verify docker daemon is running:\n'
            '   ```bash\n'
            '   sudo systemctl status docker\n'
            '   sudo systemctl start docker  # If not running\n'
            '   ```',
            
            '3. Check socket permissions:\n'
            '   ```bash\n'
            '   ls -la /var/run/docker.sock\n'
            '   # Should show: srw-rw---- 1 root docker\n'
            '   sudo chmod 666 /var/run/docker.sock  # Temporary fix\n'
            '   ```',
        ],
        priority=1,
    ),
    
    # === NODE/NPM ERRORS ===
    ErrorSolution(
        pattern=r'node: not found|node: command not found',
        name='Node.js Not Installed',
        causes=[
            'Node.js is not installed on Jenkins agent',
            'Node.js not in PATH',
            'Wrong Node version or NodeSource repo not added',
        ],
        solutions=[
            '1. Install Node.js (latest LTS):\n'
            '   ```bash\n'
            '   # Ubuntu/Debian:\n'
            '   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -\n'
            '   sudo apt-get install -y nodejs\n'
            '   ```',
            
            '2. Or use NVM (Node Version Manager):\n'
            '   ```bash\n'
            '   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash\n'
            '   nvm install --lts\n'
            '   nvm use --lts\n'
            '   ```',
            
            '3. Verify installation:\n'
            '   ```bash\n'
            '   node --version\n'
            '   npm --version\n'
            '   which node  # Should print path\n'
            '   ```',
        ],
        priority=1,
    ),
    
    ErrorSolution(
        pattern=r'npm: not found|npm: command not found',
        name='NPM Not Installed',
        causes=[
            'NPM not installed (usually comes with Node.js)',
            'NPM not in PATH',
        ],
        solutions=[
            '1. Install/reinstall Node.js (includes npm):\n'
            '   ```bash\n'
            '   sudo apt-get install -y nodejs npm\n'
            '   ```',
            
            '2. Or install npm separately:\n'
            '   ```bash\n'
            '   sudo apt-get install npm\n'
            '   npm --version  # Verify\n'
            '   ```',
        ],
        priority=1,
    ),
    
    # === PYTHON ERRORS ===
    ErrorSolution(
        pattern=r'python: not found|python: command not found|python3: not found',
        name='Python Not Installed',
        causes=[
            'Python is not installed',
            'Python not in PATH',
            'Using "python" instead of "python3" (common on Linux)',
        ],
        solutions=[
            '1. Install Python 3:\n'
            '   ```bash\n'
            '   sudo apt-get install python3 python3-pip\n'
            '   ```',
            
            '2. Create python symlink (if needed):\n'
            '   ```bash\n'
            '   sudo ln -s /usr/bin/python3 /usr/bin/python\n'
            '   ```',
            
            '3. Verify installation:\n'
            '   ```bash\n'
            '   python --version\n'
            '   python3 --version\n'
            '   which python3\n'
            '   ```',
        ],
        priority=1,
    ),
    
    # === EXIT CODE 127 (Generic) ===
    ErrorSolution(
        pattern=r'exit code 127|script returned exit code 127',
        name='Command Not Found (Exit Code 127)',
        causes=[
            'Command/tool not installed',
            'Command not in PATH',
            'Typo in command name',
            'Missing environment setup',
        ],
        solutions=[
            '1. Check which command failed in the log above this error',
            
            '2. Install missing tool:\n'
            '   ```bash\n'
            '   # For Ubuntu/Debian:\n'
            '   sudo apt-get update\n'
            '   sudo apt-get install <tool-name>\n'
            '   ```',
            
            '3. Verify PATH contains tool location:\n'
            '   ```bash\n'
            '   echo $PATH\n'
            '   which <command>  # Should return path\n'
            '   ```',
            
            '4. If using custom tools, add to PATH in Jenkins job:\n'
            '   ```groovy\n'
            '   environment {\n'
            '       PATH = "/custom/path/bin:$PATH"\n'
            '   }\n'
            '   ```',
        ],
        priority=2,
    ),
    
    # === PERMISSION ERRORS ===
    ErrorSolution(
        pattern=r'permission denied|eacces|cannot open.*permission',
        name='Permission Denied',
        causes=[
            'Insufficient file/directory permissions',
            'User not in required group (e.g., docker)',
            'SELinux blocking access (on RHEL/CentOS)',
        ],
        solutions=[
            '1. Check file permissions:\n'
            '   ```bash\n'
            '   ls -la <file-or-directory>\n'
            '   ```',
            
            '2. Fix permissions (if safe):\n'
            '   ```bash\n'
            '   # For files:\n'
            '   chmod 644 <file>\n'
            '   # For executable scripts:\n'
            '   chmod +x <script>\n'
            '   # For directories:\n'
            '   chmod 755 <directory>\n'
            '   ```',
            
            '3. Add user to required group:\n'
            '   ```bash\n'
            '   sudo usermod -aG <group-name> jenkins\n'
            '   sudo systemctl restart jenkins\n'
            '   ```',
            
            '4. Check SELinux (if on RHEL/CentOS):\n'
            '   ```bash\n'
            '   getenforce  # Check if enabled\n'
            '   sudo setenforce 0  # Temporary disable for testing\n'
            '   ```',
        ],
        priority=2,
    ),
    
    # === NETWORK ERRORS ===
    ErrorSolution(
        pattern=r'econnrefused|connection refused',
        name='Connection Refused',
        causes=[
            'Service not running (e.g., database, API server)',
            'Firewall blocking connection',
            'Wrong host/port configuration',
            'Service listening on localhost only (not 0.0.0.0)',
        ],
        solutions=[
            '1. Verify service is running:\n'
            '   ```bash\n'
            '   # Check process:\n'
            '   ps aux | grep <service-name>\n'
            '   # Check port listening:\n'
            '   sudo netstat -tulpn | grep <port>\n'
            '   # OR using ss:\n'
            '   sudo ss -tulpn | grep <port>\n'
            '   ```',
            
            '2. Start service if not running:\n'
            '   ```bash\n'
            '   sudo systemctl start <service-name>\n'
            '   sudo systemctl status <service-name>\n'
            '   ```',
            
            '3. Check firewall rules:\n'
            '   ```bash\n'
            '   # UFW (Ubuntu):\n'
            '   sudo ufw status\n'
            '   sudo ufw allow <port>\n'
            '   # Firewalld (RHEL/CentOS):\n'
            '   sudo firewall-cmd --list-all\n'
            '   sudo firewall-cmd --add-port=<port>/tcp --permanent\n'
            '   ```',
            
            '4. Verify service binds to correct interface:\n'
            '   ```bash\n'
            '   # Should listen on 0.0.0.0:<port>, not 127.0.0.1:<port>\n'
            '   sudo netstat -tulpn | grep <port>\n'
            '   ```',
        ],
        priority=3,
    ),
    
    ErrorSolution(
        pattern=r'timeout|timed out|etimedout',
        name='Network Timeout',
        causes=[
            'Slow network connection',
            'Service overloaded or unresponsive',
            'DNS resolution issues',
            'Firewall dropping packets',
        ],
        solutions=[
            '1. Increase timeout in config:\n'
            '   ```groovy\n'
            '   // In Jenkinsfile:\n'
            '   timeout(time: 30, unit: \'MINUTES\') {\n'
            '       // your build steps\n'
            '   }\n'
            '   ```',
            
            '2. Check network connectivity:\n'
            '   ```bash\n'
            '   ping <host>\n'
            '   traceroute <host>\n'
            '   curl -I <url>  # Test HTTP response\n'
            '   ```',
            
            '3. Check DNS resolution:\n'
            '   ```bash\n'
            '   nslookup <hostname>\n'
            '   dig <hostname>\n'
            '   ```',
            
            '4. Test service responsiveness:\n'
            '   ```bash\n'
            '   telnet <host> <port>\n'
            '   # OR:\n'
            '   nc -zv <host> <port>\n'
            '   ```',
        ],
        priority=3,
    ),
    
    # === CREDENTIAL ERRORS ===
    ErrorSolution(
        pattern=r'401|unauthorized|authentication failed',
        name='Authentication Failed (401)',
        causes=[
            'Invalid username/password',
            'Expired API token',
            'Missing authentication header',
            'Wrong authentication method (Basic vs Bearer)',
        ],
        solutions=[
            '1. Check credentials in Jenkins:\n'
            '   - Navigate to: Jenkins → Credentials → System → Global credentials\n'
            '   - Verify username/password or API token\n'
            '   - Update if expired',
            
            '2. Regenerate API token:\n'
            '   - GitHub: Settings → Developer settings → Personal access tokens\n'
            '   - GitLab: User Settings → Access Tokens\n'
            '   - Docker Hub: Account Settings → Security',
            
            '3. Verify credential ID in Jenkinsfile:\n'
            '   ```groovy\n'
            '   environment {\n'
            '       CREDENTIALS = credentials(\'your-credential-id\')\n'
            '   }\n'
            '   ```',
        ],
        priority=4,
    ),
    
    ErrorSolution(
        pattern=r'403|forbidden|access denied',
        name='Access Forbidden (403)',
        causes=[
            'Insufficient permissions/scopes',
            'IP address not whitelisted',
            'Rate limit exceeded',
            'Resource requires specific role',
        ],
        solutions=[
            '1. Check token/credential permissions:\n'
            '   - Ensure token has required scopes (repo, admin, etc.)\n'
            '   - Regenerate token with correct permissions',
            
            '2. Verify user/service account roles:\n'
            '   - Check if user has required roles in GitHub/GitLab/etc.\n'
            '   - Add user to correct team/organization',
            
            '3. Check IP whitelist (if applicable):\n'
            '   - Add Jenkins server IP to allowed list\n'
            '   - Check cloud provider firewall rules',
        ],
        priority=4,
    ),
]


class ErrorSolutionFinder:
    """Find concrete solutions for errors in logs"""
    
    def __init__(self):
        self.solutions = ERROR_SOLUTIONS
    
    def find_solutions(self, log_content: str, root_cause: Dict = None) -> List[ErrorSolution]:
        """
        Find all matching solutions for the log
        
        Args:
            log_content: Full log content
            root_cause: Optional root cause dict from RootCauseDetector
            
        Returns:
            List of matching ErrorSolution objects, sorted by priority
        """
        matches = []
        
        for solution in self.solutions:
            if solution.matches(log_content):
                matches.append(solution)
        
        # Sort by priority (lower number = higher priority)
        matches.sort(key=lambda x: x.priority)
        
        # ✅ FIX: If FATAL error detected, only show fatal-related solutions
        # Hide non-fatal ML false positives (e.g. network timeout when docker missing)
        if root_cause and root_cause.get('severity') == 'FATAL':
            fatal_error_type = root_cause.get('error_type', '')
            
            # Keep only solutions that match the fatal error type
            # Filter out unrelated solutions (e.g. network_error when missing_dependency_error is fatal)
            filtered_matches = []
            for solution in matches:
                # Check if solution name/pattern relates to fatal error
                solution_lower = solution.name.lower()
                
                # Map error types to solution keywords
                if 'missing_dependency' in fatal_error_type or 'environment_error' in fatal_error_type:
                    # Keep: docker/npm/python not found, permission errors
                    if any(keyword in solution_lower for keyword in ['not installed', 'not found', 'permission', 'missing', 'command']):
                        filtered_matches.append(solution)
                elif 'permission' in fatal_error_type:
                    if 'permission' in solution_lower or 'denied' in solution_lower:
                        filtered_matches.append(solution)
                elif 'disk' in fatal_error_type:
                    if 'disk' in solution_lower or 'space' in solution_lower:
                        filtered_matches.append(solution)
                else:
                    # For other fatal errors, keep first 2 high-priority solutions
                    if solution.priority <= 2:
                        filtered_matches.append(solution)
            
            # If filtering removed all, fallback to original matches
            matches = filtered_matches if filtered_matches else matches[:2]
        
        # ✅ FIX: Group related solutions (same root cause, different symptoms)
        return self._group_related_solutions(matches, log_content)
    
    def _group_related_solutions(self, solutions: List[ErrorSolution], log_content: str) -> List[ErrorSolution]:
        """
        Group related solutions together (e.g. docker not found + exit code 127)
        Keep only the highest priority solution from each group
        
        Args:
            solutions: List of matched solutions
            log_content: Full log to find related errors
            
        Returns:
            Deduplicated list with only primary solutions
        """
        if len(solutions) <= 1:
            return solutions
        
        # Track which solutions have been grouped
        grouped_indices = set()
        result = []
        
        for i, solution in enumerate(solutions):
            if i in grouped_indices:
                continue  # Already grouped
            
            # Check if this solution has related patterns
            if solution.related_patterns:
                # Find all related errors in log
                related_errors = solution.get_related_errors(log_content)
                
                # Mark related solutions as grouped
                for j, other_solution in enumerate(solutions):
                    if j > i and j not in grouped_indices:
                        # Check if other solution matches any related pattern
                        for related_pattern in solution.related_patterns:
                            if re.search(related_pattern, other_solution.pattern.pattern, re.IGNORECASE):
                                grouped_indices.add(j)
                                break
            
            result.append(solution)
        
        return result
    
    def format_solution(self, solution: ErrorSolution, log_content: str = "") -> str:
        """
        Format a solution for display
        
        Args:
            solution: ErrorSolution to format
            log_content: Optional log content to find related errors
        """
        output = []
        output.append(f"\n**{solution.name}**")
        
        # ✅ Show related errors if any
        if log_content and solution.related_patterns:
            related_errors = solution.get_related_errors(log_content)
            if related_errors:
                output.append("\n**Related Errors (same root cause):**")
                for err in related_errors[:3]:  # Max 3 related errors
                    output.append(f"  - {err.strip()}")
        
        output.append("\n**Common Causes:**")
        for i, cause in enumerate(solution.causes, 1):
            output.append(f"{i}. {cause}")
        
        output.append("\n**Solutions:**")
        for i, sol in enumerate(solution.solutions, 1):
            output.append(f"\n{sol}")
        
        return "\n".join(output)
    
    def format_all_solutions(self, solutions: List[ErrorSolution], max_solutions: int = 2, log_content: str = "") -> str:
        """
        Format multiple solutions for display
        
        Args:
            solutions: List of solutions to format
            max_solutions: Maximum number of solutions to show
            log_content: Optional log content to find related errors
        """
        if not solutions:
            return "No specific solutions found. Please review the error messages above."
        
        output = []
        output.append("\n🔧 **RECOMMENDED FIXES**\n")
        
        for i, solution in enumerate(solutions[:max_solutions], 1):
            if i > 1:
                output.append("\n" + "="*70 + "\n")
            output.append(self.format_solution(solution, log_content))
        
        if len(solutions) > max_solutions:
            output.append(f"\n... and {len(solutions) - max_solutions} more potential solutions")
        
        return "\n".join(output)


# Singleton instance
error_solution_finder = ErrorSolutionFinder()
