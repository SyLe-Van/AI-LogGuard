#!/usr/bin/env python3
"""
Test Script: Validate all improvements to AI-LogGuard
Tests: Root Cause Detection, Error Solutions, Stage Status, LLM Retry Logic
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.root_cause import root_cause_detector
from src.utils.error_solutions import error_solution_finder
from src.parsers.jenkins_parser import JenkinsParser
from rich.console import Console
from rich.panel import Panel

console = Console()


def test_root_cause_detection():
    """Test root cause detector with various error patterns"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]🧪 TEST 1: Root Cause Detection[/bold cyan]")
    console.print("="*70 + "\n")
    
    test_cases = [
        {
            "name": "Docker Not Found",
            "log": """
[Pipeline] { (Build Docker Image)
+ docker build -t myapp .
/var/jenkins_home/workspace/myapp@tmp/durable-123/script.sh: line 2: docker: not found
script returned exit code 127
""",
            "expected_type": "missing_dependency_error",  # ✅ UPDATED: docker not found is dependency error
        },
        {
            "name": "Permission Denied",
            "log": """
[Pipeline] { (Deploy)
+ ./deploy.sh
permission denied: /usr/local/bin/deploy.sh
script returned exit code 126
""",
            "expected_type": "permission_error",
        },
        {
            "name": "Network Timeout",
            "log": """
[Pipeline] { (Install Dependencies)
+ npm install
npm ERR! network timeout
npm ERR! network connection to registry.npmjs.org failed: ETIMEDOUT
""",
            "expected_type": "network_error",
        },
        {
            "name": "Authentication Failed",
            "log": """
[Pipeline] { (Push Docker Image)
+ docker push myapp:latest
Error: 401 Unauthorized: authentication required
""",
            "expected_type": "credential_error",  # ✅ FIXED: Use 401 pattern explicitly
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        console.print(f"[yellow]Testing: {test['name']}[/yellow]")
        
        root_cause = root_cause_detector.detect_root_cause(test['log'])
        
        if root_cause:
            console.print(f"  ✅ Root cause detected: {root_cause['error_type']}")
            console.print(f"     Line {root_cause['line_number']}: {root_cause['root_cause']}")
            
            if root_cause['error_type'] == test['expected_type']:
                console.print(f"  [green]✓ Correct type (expected: {test['expected_type']})[/green]")
                passed += 1
            else:
                console.print(f"  [red]✗ Wrong type (expected: {test['expected_type']}, got: {root_cause['error_type']})[/red]")
                failed += 1
        else:
            console.print(f"  [red]✗ No root cause detected (expected: {test['expected_type']})[/red]")
            failed += 1
        
        console.print()
    
    console.print(Panel(
        f"Passed: {passed}/{len(test_cases)}\nFailed: {failed}/{len(test_cases)}",
        title="Root Cause Detection Results",
        border_style="green" if failed == 0 else "yellow"
    ))


def test_error_solutions():
    """Test error solution finder"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]🧪 TEST 2: Error Solutions Mapping[/bold cyan]")
    console.print("="*70 + "\n")
    
    test_cases = [
        {
            "name": "Docker Not Found",
            "log": "docker: command not found\nexit code 127",
            "expected_solution": "Docker Not Installed",
        },
        {
            "name": "NPM Not Found",
            "log": "npm: command not found\nexit code 127",
            "expected_solution": "NPM Not Installed",
        },
        {
            "name": "Connection Refused",
            "log": "Error: connect ECONNREFUSED 127.0.0.1:5432",
            "expected_solution": "Connection Refused",
        },
        {
            "name": "Authentication Failed",
            "log": "Error response: 401 Unauthorized",
            "expected_solution": "Authentication Failed (401)",
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        console.print(f"[yellow]Testing: {test['name']}[/yellow]")
        
        solutions = error_solution_finder.find_solutions(test['log'])
        
        if solutions:
            console.print(f"  ✅ Found {len(solutions)} solution(s)")
            console.print(f"     Top solution: {solutions[0].name}")
            
            if solutions[0].name == test['expected_solution']:
                console.print(f"  [green]✓ Correct solution[/green]")
                passed += 1
            else:
                console.print(f"  [red]✗ Wrong solution (expected: {test['expected_solution']})[/red]")
                failed += 1
        else:
            console.print(f"  [red]✗ No solutions found (expected: {test['expected_solution']})[/red]")
            failed += 1
        
        console.print()
    
    console.print(Panel(
        f"Passed: {passed}/{len(test_cases)}\nFailed: {failed}/{len(test_cases)}",
        title="Error Solutions Results",
        border_style="green" if failed == 0 else "yellow"
    ))


def test_stage_status_detection():
    """Test improved stage status detection"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]🧪 TEST 3: Stage Status Detection[/bold cyan]")
    console.print("="*70 + "\n")
    
    test_log = """
[Pipeline] { (Build Docker Image)
+ docker build -t myapp .
/var/jenkins_home/workspace/myapp@tmp/durable-123/script.sh: line 2: docker: not found
script returned exit code 127
[Pipeline] }
[Pipeline] { (Push Docker Image)
Stage "Push Docker Image" skipped due to earlier failure(s)
[Pipeline] }
[Pipeline] { (Deploy to Production)
Stage "Deploy to Production" skipped due to earlier failure(s)
[Pipeline] }
[Pipeline] { (Declarative: Post Actions)
ERROR: Pipeline failed!
[Pipeline] }
"""
    
    parser = JenkinsParser()
    parsed = parser.parse(test_log, job_name="test")
    
    console.print(f"Total stages detected: {len(parsed.stages)}")
    
    expected_statuses = {
        "Build Docker Image": "FAILED",
        "Push Docker Image": "UNKNOWN",  # Skipped stages should be UNKNOWN, not SUCCESS
        "Deploy to Production": "UNKNOWN",
        "Declarative: Post Actions": "FAILED",
    }
    
    passed = 0
    failed = 0
    
    for stage in parsed.stages:
        stage_name = stage.name
        actual_status = stage.status.value if hasattr(stage.status, 'value') else str(stage.status)
        expected_status = expected_statuses.get(stage_name, "UNKNOWN")
        
        console.print(f"[yellow]{stage_name}[/yellow]")
        console.print(f"  Status: {actual_status}")
        
        if actual_status == expected_status:
            console.print(f"  [green]✓ Correct (expected: {expected_status})[/green]")
            passed += 1
        else:
            console.print(f"  [red]✗ Wrong (expected: {expected_status}, got: {actual_status})[/red]")
            failed += 1
        
        console.print()
    
    console.print(Panel(
        f"Passed: {passed}/{len(expected_statuses)}\nFailed: {failed}/{len(expected_statuses)}",
        title="Stage Status Detection Results",
        border_style="green" if failed == 0 else "yellow"
    ))


def test_concrete_solutions():
    """Test concrete solution formatting"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]🧪 TEST 4: Concrete Solution Formatting[/bold cyan]")
    console.print("="*70 + "\n")
    
    test_log = "docker: not found\nexit code 127"
    solutions = error_solution_finder.find_solutions(test_log)
    
    if solutions:
        console.print(f"[green]✅ Found {len(solutions)} solution(s)[/green]\n")
        
        # Format first solution
        formatted = error_solution_finder.format_solution(solutions[0])
        console.print(Panel(
            formatted,
            title="Sample Concrete Solution",
            border_style="cyan"
        ))
    else:
        console.print("[red]❌ No solutions found[/red]")


def main():
    """Run all tests"""
    console.print("\n[bold magenta]🚀 AI-LogGuard Improvement Validation[/bold magenta]")
    console.print("[dim]Testing: Root Cause Detection, Error Solutions, Stage Status, Concrete Fixes[/dim]\n")
    
    try:
        test_root_cause_detection()
        test_error_solutions()
        test_stage_status_detection()
        test_concrete_solutions()
        
        console.print("\n" + "="*70)
        console.print("[bold green]✅ All tests completed![/bold green]")
        console.print("="*70 + "\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ Test failed with error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
