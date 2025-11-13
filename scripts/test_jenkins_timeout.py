#!/usr/bin/env python3
"""
Test Jenkins Timeout Comment Filtering
Verify that "# timeout=10" comments are NOT detected as errors
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.root_cause import root_cause_detector
from rich.console import Console

console = Console()


def test_jenkins_timeout_filtering():
    """Test that Jenkins timeout comments are ignored"""
    
    test_log = """
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins agent in /var/jenkins_home/workspace/myapp
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Checkout)
[Pipeline] git
git init /var/jenkins_home/workspace/myapp # timeout=10
Fetching changes from the remote Git repository
Checking out Revision abc123 (refs/remotes/origin/main)
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Build Docker Image)
[Pipeline] sh
+ docker build -t myapp:latest .
/var/jenkins_home/workspace/myapp@tmp/durable-123/script.sh: line 1: docker: not found
script returned exit code 127
[Pipeline] }
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
ERROR: Build failed with exit code 127
Finished: FAILURE
"""
    
    console.print("\n[bold cyan]🧪 Testing Jenkins Timeout Comment Filtering[/bold cyan]\n")
    
    root_cause = root_cause_detector.detect_root_cause(test_log)
    
    if root_cause:
        console.print(f"[green]✅ Root cause detected:[/green]")
        console.print(f"   Line {root_cause['line_number']}: {root_cause['line_content']}")
        console.print(f"   Type: {root_cause['error_type']}")
        console.print(f"   Severity: {root_cause['severity']}")
        console.print(f"   Priority: {root_cause['priority']}")
        
        # Verify it's NOT the timeout comment
        if 'timeout' in root_cause['line_content'].lower() and '# timeout=' in root_cause['line_content']:
            console.print(f"\n[red]❌ FAIL: Detected Jenkins timeout comment as error![/red]")
            console.print(f"   This should have been ignored.")
            return False
        
        # Verify it IS the docker not found error
        if 'docker: not found' in root_cause['line_content']:
            console.print(f"\n[green]✅ PASS: Correctly detected 'docker: not found' as root cause[/green]")
            console.print(f"   Ignored 'git init # timeout=10' comment ✅")
            return True
        elif root_cause['error_type'] == 'environment_error' or root_cause['error_type'] == 'missing_dependency_error':
            console.print(f"\n[green]✅ PASS: Correctly classified as {root_cause['error_type']}[/green]")
            console.print(f"   (Found exit code 127 or similar)")
            return True
        else:
            console.print(f"\n[yellow]⚠️  PARTIAL: Found error but wrong type[/yellow]")
            console.print(f"   Expected: missing_dependency_error or environment_error")
            console.print(f"   Got: {root_cause['error_type']}")
            return False
    else:
        console.print(f"[red]❌ FAIL: No root cause detected![/red]")
        console.print(f"   Should have detected 'docker: not found'")
        return False


def test_network_timeout_vs_jenkins_comment():
    """Test that real timeout errors are still detected"""
    
    test_log = """
[Pipeline] Start of Pipeline
[Pipeline] { (Install Dependencies)
+ npm install
npm ERR! code ETIMEDOUT
npm ERR! errno ETIMEDOUT
npm ERR! network timeout at: https://registry.npmjs.org/react
npm ERR! network This is a timeout error from npm, not Jenkins
[Pipeline] }
"""
    
    console.print("\n[bold cyan]🧪 Testing Real Timeout Detection[/bold cyan]\n")
    
    root_cause = root_cause_detector.detect_root_cause(test_log)
    
    if root_cause:
        console.print(f"[green]✅ Root cause detected:[/green]")
        console.print(f"   Type: {root_cause['error_type']}")
        console.print(f"   Line: {root_cause['line_content']}")
        
        if root_cause['error_type'] == 'network_error':
            console.print(f"\n[green]✅ PASS: Correctly detected real network timeout[/green]")
            return True
        else:
            console.print(f"\n[yellow]⚠️  Detected error but wrong type[/yellow]")
            console.print(f"   Expected: network_error")
            console.print(f"   Got: {root_cause['error_type']}")
            return False
    else:
        console.print(f"[red]❌ FAIL: Should have detected network timeout[/red]")
        return False


def main():
    console.print("\n[bold magenta]🔍 Jenkins Timeout Comment Filtering Test[/bold magenta]\n")
    
    results = []
    
    # Test 1: Ignore Jenkins timeout comments
    results.append(test_jenkins_timeout_filtering())
    
    # Test 2: Still detect real timeout errors
    results.append(test_network_timeout_vs_jenkins_comment())
    
    # Summary
    console.print("\n" + "="*70)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        console.print(f"[bold green]✅ All tests passed ({passed}/{total})[/bold green]")
        sys.exit(0)
    else:
        console.print(f"[bold yellow]⚠️  {passed}/{total} tests passed[/bold yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()
