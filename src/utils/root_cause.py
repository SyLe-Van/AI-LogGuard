"""
Root Cause Detection
Analyze logs to find the FIRST FATAL error (root cause) and ignore downstream errors
Priority: Fatal Runtime Errors > Build Errors > Network Errors
"""
import re
from typing import Optional, Dict, List, Tuple
from ..models import LogEntry, StageInfo


class RootCauseDetector:
    """Detect root cause of build failure by finding first FATAL error"""
    
    # 🔥 FIXED PRIORITY: Fatal Runtime Errors ALWAYS win
    # Priority 1 (FATAL): Command not found, exit codes, permissions
    # Priority 2 (HIGH): Build/compilation failures  
    # Priority 3 (MEDIUM): Network/timeout errors
    
    ERROR_PATTERNS = [
        # ═══════════════════════════════════════════════════════════
        # 🥇 PRIORITY 1 - FATAL RUNTIME ERRORS (HIGHEST PRIORITY)
        # ═══════════════════════════════════════════════════════════
        
        # Exit code 127 = command not found (MOST CRITICAL)
        {
            'pattern': r'exit code 127|script returned exit code 127',
            'type': 'environment_error',
            'severity': 'FATAL',
            'root_cause': 'Command not found (exit code 127)',
            'priority': 1,
        },
        
        # Docker not found (FATAL - blocks everything)
        {
            'pattern': r'docker: not found|docker: command not found',
            'type': 'missing_dependency_error',
            'severity': 'FATAL',
            'root_cause': 'Docker is not installed or not in PATH',
            'priority': 1,
        },
        
        # Node/NPM not found
        {
            'pattern': r'node: not found|node: command not found',
            'type': 'missing_dependency_error',
            'severity': 'FATAL',
            'root_cause': 'Node.js is not installed or not in PATH',
            'priority': 1,
        },
        {
            'pattern': r'npm: not found|npm: command not found',
            'type': 'missing_dependency_error',
            'severity': 'FATAL',
            'root_cause': 'NPM is not installed or not in PATH',
            'priority': 1,
        },
        
        # Python not found
        {
            'pattern': r'python: not found|python: command not found|python3: not found',
            'type': 'missing_dependency_error',
            'severity': 'FATAL',
            'root_cause': 'Python is not installed or not in PATH',
            'priority': 1,
        },
        
        # Other critical tools
        {
            'pattern': r'java: not found|java: command not found',
            'type': 'missing_dependency_error',
            'severity': 'FATAL',
            'root_cause': 'Java is not installed or not in PATH',
            'priority': 1,
        },
        {
            'pattern': r'git: not found|git: command not found',
            'type': 'missing_dependency_error',
            'severity': 'FATAL',
            'root_cause': 'Git is not installed or not in PATH',
            'priority': 1,
        },
        {
            'pattern': r'gcc: not found|gcc: command not found',
            'type': 'missing_dependency_error',
            'severity': 'FATAL',
            'root_cause': 'GCC compiler is not installed',
            'priority': 1,
        },
        
        # Exit code 126 = permission denied
        {
            'pattern': r'exit code 126',
            'type': 'permission_error',
            'severity': 'FATAL',
            'root_cause': 'Command cannot execute - permission denied (exit code 126)',
            'priority': 1,
        },
        
        # Permission errors
        {
            'pattern': r'permission denied|eacces|cannot open.*permission',
            'type': 'permission_error',
            'severity': 'FATAL',
            'root_cause': 'Permission denied - insufficient access rights',
            'priority': 1,
        },
        
        # Disk space errors
        {
            'pattern': r'no space left on device|enospc',
            'type': 'environment_error',
            'severity': 'FATAL',
            'root_cause': 'No space left on device',
            'priority': 1,
        },
        
        # File not found (critical files)
        {
            'pattern': r'no such file or directory.*dockerfile|dockerfile.*not found',
            'type': 'environment_error',
            'severity': 'FATAL',
            'root_cause': 'Dockerfile not found',
            'priority': 1,
        },
        
        # ═══════════════════════════════════════════════════════════
        # 🥈 PRIORITY 2 - BUILD/COMPILATION ERRORS
        # ═══════════════════════════════════════════════════════════
        
        # Build failures
        {
            'pattern': r'build failed|compilation failed|failed to compile',
            'type': 'build_error',
            'severity': 'HIGH',
            'root_cause': 'Build/compilation failed',
            'priority': 2,
        },
        
        # Next.js/React build errors
        {
            'pattern': r'next\.js.*error|failed to load next config',
            'type': 'build_error',
            'severity': 'HIGH',
            'root_cause': 'Next.js build error',
            'priority': 2,
        },
        
        # Docker build errors
        {
            'pattern': r'failed to solve|failed to compute cache key',
            'type': 'docker_build_error',
            'severity': 'HIGH',
            'root_cause': 'Docker build failed - Dockerfile issue',
            'priority': 2,
        },
        {
            'pattern': r'error response from daemon',
            'type': 'docker_build_error',
            'severity': 'HIGH',
            'root_cause': 'Docker daemon error',
            'priority': 2,
        },
        
        # Syntax errors
        {
            'pattern': r'syntaxerror|syntax error',
            'type': 'syntax_error',
            'severity': 'HIGH',
            'root_cause': 'Syntax error in code',
            'priority': 2,
        },
        
        # Module/dependency errors (missing imports, not command-line tools)
        {
            'pattern': r'modulenotfounderror|module .* not found|cannot find module',
            'type': 'dependency_error',
            'severity': 'HIGH',
            'root_cause': 'Missing dependency - module not installed',
            'priority': 2,
        },
        
        # Test failures
        {
            'pattern': r'test failed|unit test|tests? failed',
            'type': 'test_failure',
            'severity': 'MEDIUM',
            'root_cause': 'Unit/integration test failed',
            'priority': 2,
        },
        
        # ═══════════════════════════════════════════════════════════
        # 🥉 PRIORITY 3 - NETWORK/TIMEOUT ERRORS (LOWEST PRIORITY)
        # ═══════════════════════════════════════════════════════════
        
        # Connection refused
        {
            'pattern': r'econnrefused|connection refused',
            'type': 'network_error',
            'severity': 'MEDIUM',
            'root_cause': 'Connection refused - service not running or blocked',
            'priority': 3,
        },
        
        # Timeout errors (LOWEST PRIORITY - often secondary issues)
        {
            'pattern': r'(?<!#\s)(?<!# )timeout(?!\s*=)|timed out|etimedout|npm err.*network.*timeout',  # ✅ Exclude Jenkins "# timeout=10"
            'type': 'network_error',
            'severity': 'MEDIUM',
            'root_cause': 'Network timeout - slow connection or unreachable service',
            'priority': 3,
        },
        
        # Network unreachable
        {
            'pattern': r'no route to host|network unreachable',
            'type': 'network_error',
            'severity': 'MEDIUM',
            'root_cause': 'Network unreachable - routing issue',
            'priority': 3,
        },
        
        # Credential errors
        {
            'pattern': r'401|unauthorized|authentication failed',
            'type': 'credential_error',
            'severity': 'HIGH',
            'root_cause': 'Authentication failed - invalid credentials',
            'priority': 3,
        },
        {
            'pattern': r'403|forbidden|access denied',
            'type': 'credential_error',
            'severity': 'HIGH',
            'root_cause': 'Access forbidden - insufficient permissions',
            'priority': 3,
        },
    ]
    
    # ✅ IGNORE PATTERNS - These are NOT root causes
    IGNORE_PATTERNS = [
        r'stage.*skipped',  # Skipped stages are consequences
        r'post actions?',  # Post actions are cleanup
        r'declarative: post',  # Jenkins post-build actions
        r'archiving artifacts',  # Artifact archival
        r'cleanup',  # Cleanup tasks
        r'publishing',  # Publishing tasks
        r'# timeout=\d+',  # ✅ FIX: Ignore Jenkins timeout comments
        r'git init.*# timeout',  # ✅ FIX: Ignore git init timeout parameter
    ]
    
    def __init__(self):
        # Compile regex patterns for performance
        self.compiled_patterns = [
            {
                **pattern,
                'regex': re.compile(pattern['pattern'], re.IGNORECASE)
            }
            for pattern in self.ERROR_PATTERNS
        ]
        
        self.ignore_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.IGNORE_PATTERNS
        ]
    
    def _should_ignore_line(self, line: str) -> bool:
        """Check if line should be ignored"""
        return any(ignore.search(line) for ignore in self.ignore_regex)
    
    def _extract_context(self, lines: List[str], target_line_num: int, context_lines: int = 3) -> Tuple[str, int, int]:
        """
        Extract context around error line (±3 lines)
        
        Returns:
            (context_text, start_line, end_line)
        """
        start = max(0, target_line_num - context_lines - 1)
        end = min(len(lines), target_line_num + context_lines)
        
        context = lines[start:end]
        return '\n'.join(context), start + 1, end
    
    def detect_root_cause(
        self, 
        log_content: str, 
        errors: List[LogEntry] = None,
        stages: List[StageInfo] = None
    ) -> Optional[Dict]:
        """
        Detect root cause by finding the FIRST FATAL error
        
        Strategy:
        1. Scan log line by line
        2. Skip ignored patterns (Jenkins comments, skipped stages, etc.)
        3. Match patterns in PRIORITY order (Priority 1 = FATAL)
        4. Return FIRST match with HIGHEST priority
        5. Include ±3 lines context around error
        
        Args:
            log_content: Full log content
            errors: List of detected errors
            stages: List of stages (to identify failed stage)
            
        Returns:
            Dict with root cause information or None
        """
        lines = log_content.splitlines()
        
        # Track FIRST error found (by priority, then by line number)
        first_error_line = None
        first_error_pattern = None
        first_error_line_num = float('inf')
        current_stage = None
        
        # 🔥 FIX: Scan log to find FIRST FATAL error (Priority 1)
        # Then if none found, find first Priority 2, then Priority 3
        for priority_level in [1, 2, 3]:
            for line_num, line in enumerate(lines, start=1):
                # Skip already processed lines
                if line_num >= first_error_line_num:
                    continue
                
                line_lower = line.lower()
                
                # Track current stage
                stage_match = re.search(r'\[Pipeline\] \{ \(([^)]+)\)', line)
                if stage_match:
                    current_stage = stage_match.group(1)
                
                # ✅ FIX 1: Skip ignored patterns (Jenkins comments, etc.)
                if self._should_ignore_line(line):
                    continue
                
                # Check error patterns for this priority level
                for pattern_info in [p for p in self.compiled_patterns if p['priority'] == priority_level]:
                    if pattern_info['regex'].search(line_lower):
                        # Found an error at this priority level!
                        if line_num < first_error_line_num:
                            first_error_line = line
                            first_error_pattern = pattern_info
                            first_error_line_num = line_num
                            # Don't break - continue to check if there's an earlier error at same priority
            
            # If we found an error at this priority level, stop searching lower priorities
            if first_error_pattern:
                break
        
        # If no pattern matched, try to find first explicit error
        if not first_error_pattern and errors and len(errors) > 0:
            first_error = errors[0]
            
            # ✅ FIX 3: Extract context around error
            context, start_line, end_line = self._extract_context(lines, first_error.line_number)
            
            return {
                'line_number': first_error.line_number,
                'line_content': first_error.message,
                'context': context,
                'context_lines': f"Lines {start_line}-{end_line}",
                'error_type': 'unknown_error',
                'severity': 'MEDIUM',
                'root_cause': 'Build failed - see first error above',
                'stage': current_stage,
                'priority': 99,
            }
        
        if not first_error_pattern:
            return None
        
        # ✅ FIX 3: Extract ±3 lines context around root cause
        context, start_line, end_line = self._extract_context(lines, first_error_line_num)
        
        # ✅ FIX: Find ACTUAL stage containing error (not just first FAILED stage)
        # Parse log to find stage boundaries and locate stage containing error_line
        failed_stage = None
        stage_map = {}  # {stage_name: (start_line, end_line)}
        current_parsing_stage = None
        current_stage_start = 0
        
        for idx, line in enumerate(lines, start=1):
            # Detect stage start: [Pipeline] { (stage-name)
            stage_start_match = re.search(r'\[Pipeline\] \{ \(([^)]+)\)', line)
            if stage_start_match:
                stage_name = stage_start_match.group(1)
                # Close previous stage
                if current_parsing_stage:
                    stage_map[current_parsing_stage] = (current_stage_start, idx - 1)
                # Start new stage
                current_parsing_stage = stage_name
                current_stage_start = idx
            
            # Detect stage end: [Pipeline] }
            elif '[Pipeline] }' in line and current_parsing_stage:
                stage_map[current_parsing_stage] = (current_stage_start, idx)
                current_parsing_stage = None
        
        # Close last stage if still open
        if current_parsing_stage:
            stage_map[current_parsing_stage] = (current_stage_start, len(lines))
        
        # Find which stage contains the error line
        for stage_name, (start, end) in stage_map.items():
            if start <= first_error_line_num <= end:
                # ✅ Ignore "Post Actions" and "Declarative: Post Actions"
                if 'post action' not in stage_name.lower():
                    failed_stage = stage_name
                    break
        
        # Fallback: use current_stage from scan if no stage found
        if not failed_stage and current_stage:
            if 'post action' not in current_stage.lower():
                failed_stage = current_stage
        
        return {
            'line_number': first_error_line_num,
            'line_content': first_error_line.strip(),
            'context': context,  # ✅ FIX 3: Include context
            'context_lines': f"Lines {start_line}-{end_line}",
            'error_type': first_error_pattern['type'],
            'severity': first_error_pattern['severity'],
            'root_cause': first_error_pattern['root_cause'],
            'stage': failed_stage or "Unknown",
            'priority': first_error_pattern['priority'],
        }
    
    def format_root_cause(self, root_cause: Dict) -> str:
        """Format root cause for display"""
        if not root_cause:
            return "No specific root cause detected"
        
        severity_icon = {
            'FATAL': '🔴',
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
        }.get(root_cause['severity'], '⚪')
        
        output = []
        output.append(f"\n{severity_icon} **ROOT CAUSE DETECTED** ({root_cause['severity']} priority)")
        output.append(f"📍 Line {root_cause['line_number']}: {root_cause['line_content']}")
        
        # ✅ FIX 3: Include context
        if root_cause.get('context'):
            output.append(f"\n**Error Context ({root_cause['context_lines']}):**")
            output.append(f"```\n{root_cause['context']}\n```")
        
        output.append(f"\n🔍 Analysis: {root_cause['root_cause']}")
        output.append(f"🏷️  Error Type: {root_cause['error_type']}")
        if root_cause.get('stage'):
            output.append(f"🎯 Failed Stage: {root_cause['stage']}")
        
        return "\n".join(output)


# Singleton instance
root_cause_detector = RootCauseDetector()
