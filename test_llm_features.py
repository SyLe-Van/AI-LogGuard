#!/usr/bin/env python3
"""
Test script for Phase 2 LLM features
Tests OpenAI integration with real Jenkins logs
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Import Phase 1
from src.parsers import parse_log

# Import Phase 2
from src.llm.openai_client import OpenAIClient
from src.llm.summarizer import LogSummarizer
from src.llm.explainer import ErrorExplainer
from src.llm.fix_suggester import FixSuggester
from src.cache.cache_manager import CacheManager

console = Console()


def test_openai_connection():
    """Test OpenAI API connection"""
    console.print("\n[bold blue]🔌 Testing OpenAI Connection...[/bold blue]\n")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]❌ OPENAI_API_KEY not found in environment[/red]")
        console.print("[yellow]Set it with: export OPENAI_API_KEY='your-key'[/yellow]")
        return False
    
    try:
        client = OpenAIClient(api_key=api_key)
        console.print(f"[green]✅ OpenAI client initialized[/green]")
        console.print(f"   Model: {client.model}")
        console.print(f"   Temperature: {client.temperature}")
        return client
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize OpenAI client: {e}[/red]")
        return False


def test_summarizer(client, parsed_log):
    """Test log summarization"""
    console.print("\n[bold blue]📝 Testing Log Summarizer...[/bold blue]\n")
    
    try:
        summarizer = LogSummarizer(client)
        
        console.print("[yellow]⏳ Calling OpenAI API (this may take a few seconds)...[/yellow]")
        summary = summarizer.summarize(parsed_log)
        
        console.print("[green]✅ Summary generated successfully![/green]\n")
        
        # Display summary
        console.print(Panel(
            f"[bold]STATUS:[/bold] {summary.status}\n\n"
            f"[bold]MAIN ISSUE:[/bold]\n{summary.main_issue}\n\n"
            f"[bold]KEY POINTS:[/bold]\n" + 
            "\n".join(f"  • {point}" for point in summary.key_points) +
            f"\n\n[bold]IMPACT:[/bold] {summary.impact}\n"
            f"[bold]CONFIDENCE:[/bold] {summary.confidence}%",
            title="🤖 AI Summary",
            border_style="blue",
        ))
        
        return summary
    except Exception as e:
        console.print(f"[red]❌ Summarizer failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def test_explainer(client, parsed_log):
    """Test error explanation"""
    console.print("\n[bold blue]🔍 Testing Error Explainer...[/bold blue]\n")
    
    if not parsed_log.errors:
        console.print("[yellow]⚠️  No errors to explain[/yellow]")
        return None
    
    try:
        explainer = ErrorExplainer(client)
        
        # Explain first error
        error = parsed_log.errors[0]
        console.print(f"[yellow]Explaining error at line {error.line_number}...[/yellow]")
        console.print(f"Error: {error.message[:100]}...\n")
        
        explanation = explainer.explain(error, parsed_log)
        
        console.print("[green]✅ Explanation generated![/green]\n")
        
        # Display explanation
        console.print(Panel(
            f"[bold]ROOT CAUSE:[/bold]\n{explanation.root_cause}\n\n"
            f"[bold]COMMON SCENARIOS:[/bold]\n" +
            "\n".join(f"  • {s}" for s in explanation.common_scenarios) +
            f"\n\n[bold]TECHNICAL DETAILS:[/bold]\n{explanation.technical_details}\n\n"
            f"[bold]CONFIDENCE:[/bold] {explanation.confidence}%",
            title="🔍 Error Explanation",
            border_style="yellow",
        ))
        
        return explanation
    except Exception as e:
        console.print(f"[red]❌ Explainer failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def test_fix_suggester(client, parsed_log):
    """Test fix suggestions"""
    console.print("\n[bold blue]💡 Testing Fix Suggester...[/bold blue]\n")
    
    if not parsed_log.errors:
        console.print("[yellow]⚠️  No errors to fix[/yellow]")
        return None
    
    try:
        fixer = FixSuggester(client)
        
        # Get fix for first error
        error = parsed_log.errors[0]
        console.print(f"[yellow]Generating fix for error at line {error.line_number}...[/yellow]\n")
        
        fix_plan = fixer.suggest_fix(error, parsed_log)
        
        console.print("[green]✅ Fix plan generated![/green]\n")
        
        # Display fix plan
        fix_text = f"[bold]DIAGNOSIS:[/bold]\n{fix_plan.diagnosis}\n\n"
        
        if fix_plan.quick_fix:
            fix_text += f"[bold]QUICK FIX:[/bold]\n```bash\n{fix_plan.quick_fix}\n```\n\n"
        
        fix_text += "[bold]DETAILED STEPS:[/bold]\n"
        for i, step in enumerate(fix_plan.detailed_steps, 1):
            fix_text += f"  {i}. {step}\n"
        
        if fix_plan.code_changes:
            fix_text += "\n[bold]CODE CHANGES:[/bold]\n"
            for filename, code in fix_plan.code_changes.items():
                fix_text += f"\nFile: `{filename}`\n```\n{code}\n```\n"
        
        if fix_plan.prevention_tips:
            fix_text += "\n[bold]PREVENTION:[/bold]\n"
            fix_text += "\n".join(f"  • {tip}" for tip in fix_plan.prevention_tips)
        
        fix_text += f"\n\n[bold]CONFIDENCE:[/bold] {fix_plan.confidence}%"
        
        console.print(Panel(
            fix_text,
            title="💡 Fix Suggestions",
            border_style="green",
        ))
        
        return fix_plan
    except Exception as e:
        console.print(f"[red]❌ Fix suggester failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def test_caching(client, parsed_log):
    """Test cache functionality"""
    console.print("\n[bold blue]💾 Testing Cache Manager...[/bold blue]\n")
    
    try:
        cache = CacheManager()
        console.print(f"[green]✅ Cache initialized at: {cache.cache_dir}[/green]\n")
        
        # Test with summarizer
        summarizer = LogSummarizer(client)
        
        # First call (cache miss)
        console.print("[yellow]First call (should be cache MISS)...[/yellow]")
        cache_key = parsed_log.raw_content or ""
        
        cached = cache.get(cache_key, "summaries")
        if cached:
            console.print("[red]❌ Unexpected cache hit on first call[/red]")
        else:
            console.print("[green]✅ Cache MISS (expected)[/green]")
        
        # Generate and cache
        console.print("[yellow]Generating summary...[/yellow]")
        summary = summarizer.summarize(parsed_log)
        cache.set(cache_key, summary, "summaries")
        console.print("[green]✅ Summary cached[/green]\n")
        
        # Second call (cache hit)
        console.print("[yellow]Second call (should be cache HIT)...[/yellow]")
        cached = cache.get(cache_key, "summaries")
        
        if cached:
            console.print("[green]✅ Cache HIT! (saved API call)[/green]")
            console.print(f"   Cached status: {cached.status}")
            console.print(f"   Cached main_issue: {cached.main_issue[:50]}...")
        else:
            console.print("[red]❌ Expected cache hit but got miss[/red]")
        
        # Show stats
        stats = cache.get_stats()
        console.print("\n[bold cyan]Cache Statistics:[/bold cyan]")
        console.print(f"  Hits: {stats['hits']}")
        console.print(f"  Misses: {stats['misses']}")
        console.print(f"  Hit Rate: {stats['hit_rate']:.1f}%")
        console.print(f"  Cached items: {sum(stats['cache_sizes'].values())}")
        
        return True
    except Exception as e:
        console.print(f"[red]❌ Cache test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_cost_tracking(client):
    """Test cost tracking"""
    console.print("\n[bold blue]💰 Testing Cost Tracking...[/bold blue]\n")
    
    try:
        stats = client.get_usage_stats()
        
        console.print("[bold cyan]API Usage Statistics:[/bold cyan]")
        console.print(f"  Total Requests: {stats['total_requests']}")
        console.print(f"  Total Tokens: {stats['total_tokens']:,}")
        console.print(f"  Estimated Cost: ${stats['estimated_cost']:.4f}")
        console.print(f"  Model: {stats['model']}")
        
        return True
    except Exception as e:
        console.print(f"[red]❌ Cost tracking failed: {e}[/red]")
        return False


def main():
    """Main test function"""
    console.print(Panel.fit(
        "[bold green]🧪 AI-LogGuard Phase 2 Test Suite[/bold green]\n"
        "Testing LLM features with real OpenAI API",
        border_style="green",
    ))
    
    # Check for log file
    log_file = Path("jenkins-test.log")
    if not log_file.exists():
        console.print(f"\n[red]❌ Log file not found: {log_file}[/red]")
        console.print("[yellow]Run ./test_jenkins.sh first to fetch logs[/yellow]")
        return 1
    
    console.print(f"\n[green]✅ Using log file: {log_file}[/green]")
    
    # Parse log (Phase 1)
    console.print("\n[bold blue]📋 Phase 1: Parsing Log...[/bold blue]\n")
    try:
        with open(log_file) as f:
            log_content = f.read()
        
        parsed = parse_log(log_content, job_name="jenkins-test")
        console.print(f"[green]✅ Log parsed successfully[/green]")
        console.print(f"   Platform: {parsed.platform.value}")
        console.print(f"   Status: {parsed.status.value}")
        console.print(f"   Errors: {parsed.error_count}")
        console.print(f"   Warnings: {parsed.warning_count}")
    except Exception as e:
        console.print(f"[red]❌ Failed to parse log: {e}[/red]")
        return 1
    
    # Test OpenAI connection
    client = test_openai_connection()
    if not client:
        return 1
    
    # Run all tests
    console.print("\n" + "="*60)
    console.print("[bold cyan]🚀 Running Phase 2 Tests[/bold cyan]")
    console.print("="*60)
    
    # Test 1: Summarizer
    summary = test_summarizer(client, parsed)
    
    # Test 2: Explainer
    explanation = test_explainer(client, parsed)
    
    # Test 3: Fix Suggester
    fix_plan = test_fix_suggester(client, parsed)
    
    # Test 4: Caching
    cache_ok = test_caching(client, parsed)
    
    # Test 5: Cost Tracking
    cost_ok = test_cost_tracking(client)
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Test Summary[/bold green]")
    console.print("="*60 + "\n")
    
    results = [
        ("OpenAI Connection", client is not False),
        ("Log Summarizer", summary is not None),
        ("Error Explainer", explanation is not None),
        ("Fix Suggester", fix_plan is not None),
        ("Cache Manager", cache_ok),
        ("Cost Tracking", cost_ok),
    ]
    
    for test_name, passed in results:
        status = "[green]✅ PASSED[/green]" if passed else "[red]❌ FAILED[/red]"
        console.print(f"  {test_name:<30} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    console.print(f"\n[bold]Results: {passed_count}/{total} tests passed[/bold]")
    
    if passed_count == total:
        console.print("\n[bold green]🎉 All tests passed! Phase 2 is ready![/bold green]\n")
        return 0
    else:
        console.print("\n[bold yellow]⚠️  Some tests failed. Check errors above.[/bold yellow]\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Tests interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
