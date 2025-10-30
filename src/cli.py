"""
AI-LogGuard CLI - Modern CLI interface built with Typer
Main entry point for the application
"""
import sys
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
import json

from .parsers import parse_log
from .models import ParsedLog, BuildStatus, Platform
from .utils.display import display_parsed_log, display_summary

# Phase 2: LLM imports (conditional)
try:
    from .llm.gemini_client import GeminiClient
    from .llm.summarizer import LogSummarizer
    from .llm.explainer import ErrorExplainer
    from .llm.fix_suggester import FixSuggester
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    GeminiClient = None

# Cache manager (optional, can work without it)
try:
    from .cache.cache_manager import CacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    CacheManager = None

# Create Typer app
app = typer.Typer(
    name="ai-logguard",
    help="🤖 AI-powered CLI for CI/CD log analysis, failure prediction, and auto-fix suggestions",
    add_completion=False,
)

# Rich console for beautiful output
console = Console()


@app.command()
def analyze(
    log_file: Path = typer.Argument(
        ...,
        help="Path to the CI/CD log file to analyze",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_format: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help="Output format: rich, json, markdown",
    ),
    show_full: bool = typer.Option(
        False,
        "--full",
        help="Show full analysis including all errors and warnings",
    ),
    use_llm: bool = typer.Option(
        False,
        "--llm",
        help="[Phase 2] Enable AI-powered analysis with Google Gemini (FREE!)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="[Phase 2] Bypass cache for LLM responses",
    ),
    model: str = typer.Option(
        "gemini-2.5-flash",
        "--model",
        help="[Phase 2] Gemini model to use (gemini-2.5-flash, gemini-2.5-pro)",
    ),
):
    """
    🔍 Analyze a CI/CD log file
    
    Parse and analyze logs from Jenkins, GitHub Actions, GitLab CI, etc.
    
    \b
    Phase 1 (default): Rule-based analysis (FREE)
    Phase 2 (--llm):   AI-powered insights with Google Gemini (FREE, Cloud API)
    """
    console.print(f"\n[bold blue]🔍 Analyzing log file:[/bold blue] {log_file}\n")
    
    # Read log file
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Reading log file...", total=None)
        
        try:
            log_content = log_file.read_text(encoding='utf-8')
            progress.update(task, description="✅ Log file loaded")
        except Exception as e:
            console.print(f"[red]❌ Error reading file: {e}[/red]")
            raise typer.Exit(code=1)
    
    # Parse log
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Parsing log...", total=None)
        
        try:
            parsed = parse_log(
                log_content,
                job_name=log_file.stem,
            )
            progress.update(task, description="✅ Log parsed successfully")
        except Exception as e:
            console.print(f"[red]❌ Error parsing log: {e}[/red]")
            raise typer.Exit(code=1)
    
    console.print()
    
    # Phase 1: Rule-based analysis
    if output_format == "json":
        console.print(json.dumps(parsed.model_dump(), indent=2, default=str))
    elif output_format == "markdown":
        _display_markdown(parsed)
    else:  # rich (default)
        display_parsed_log(parsed, console=console, show_full=show_full)
    
    # Phase 2: AI-powered analysis
    if use_llm:
        _run_llm_analysis(parsed, log_content, model, no_cache, show_full)
    elif parsed.status == BuildStatus.FAILED and parsed.error_count > 0:
        console.print(f"\n[yellow]💡 Tip: Add --llm for AI-powered error analysis[/yellow]")
    
    console.print()


@app.command()
def summarize(
    log_file: Path = typer.Argument(
        ...,
        help="Path to the CI/CD log file to summarize",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    📊 Generate a quick summary of a log file
    
    Show high-level statistics and key information.
    """
    console.print(f"\n[bold blue]📊 Summarizing log file:[/bold blue] {log_file}\n")
    
    # Read and parse
    try:
        log_content = log_file.read_text(encoding='utf-8')
        parsed = parse_log(log_content, job_name=log_file.stem)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Display summary
    display_summary(parsed, console=console)
    console.print()


@app.command()
def fetch(
    provider: str = typer.Option(
        ...,
        "--provider",
        "-p",
        help="CI/CD provider: jenkins, github-actions, gitlab-ci",
    ),
    url: str = typer.Option(
        ...,
        "--url",
        "-u",
        help="Base URL of CI/CD instance",
    ),
    job_id: str = typer.Option(
        ...,
        "--job-id",
        "-j",
        help="Job/workflow ID or name",
    ),
    token: str = typer.Option(
        ...,
        "--token",
        "-t",
        help="API token for authentication",
    ),
    username: str = typer.Option(
        "admin",
        "--username",
        help="Username for authentication",
    ),
    build_number: str = typer.Option(
        "lastBuild",
        "--build",
        "-b",
        help="Build number or 'lastBuild'",
    ),
    save_to: Optional[Path] = typer.Option(
        None,
        "--save",
        "-s",
        help="Save fetched logs to file",
    ),
):
    """
    📥 Fetch logs directly from CI/CD platform
    
    Fetch logs from Jenkins, GitHub Actions, etc. and optionally save to file.
    """
    console.print(f"\n[bold blue]📥 Fetching logs from {provider}[/bold blue]\n")
    
    provider_lower = provider.lower()
    
    if provider_lower == "jenkins":
        from .fetchers.jenkins_fetcher import JenkinsFetcher
        
        with console.status("[bold green]Fetching from Jenkins..."):
            try:
                fetcher = JenkinsFetcher(url, token, username)
                logs = fetcher.get_logs(job_id, build_number)
                console.print("✅ Logs fetched successfully")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                raise typer.Exit(code=1)
    else:
        console.print(f"[red]❌ Provider '{provider}' not supported yet[/red]")
        raise typer.Exit(code=1)
    
    # Save to file if requested
    if save_to:
        save_to.write_text(logs, encoding='utf-8')
        console.print(f"💾 Saved to: {save_to}")
    else:
        # Display preview
        console.print("\n[bold]Preview (first 500 chars):[/bold]")
        console.print(Panel(logs[:500] + "...", title="Fetched Logs"))
    
    console.print()


@app.command()
def version(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed version information",
    )
):
    """📦 Show version information"""
    console.print("\n[bold blue]AI-LogGuard[/bold blue] v1.0.0")
    console.print("AI-powered CI/CD log analysis tool\n")
    
    if verbose:
        console.print("[bold]Phase 1 Features:[/bold]")
        console.print("  [green]✅[/green] Jenkins & GitHub Actions parsing")
        console.print("  [green]✅[/green] Error detection and categorization")
        console.print("  [green]✅[/green] Build status analysis")
        console.print("  [green]✅[/green] Stage-level insights\n")
        
        if LLM_AVAILABLE:
            console.print("[bold]Phase 2 Features (100% FREE!):[/bold]")
            console.print("  [green]✅[/green] AI-powered summaries (Google Gemini)")
            console.print("  [green]✅[/green] Error explanations (Cloud API)")
            console.print("  [green]✅[/green] Fix suggestions (No setup needed)")
            if CACHE_AVAILABLE:
                console.print("  [green]✅[/green] Response caching (Faster repeats)")
            console.print("  [cyan]🎉[/cyan] Powered by Gemini 2.5 Flash\n")
        else:
            console.print("[bold]Phase 2 Features:[/bold]")
            console.print("  [dim]⬜[/dim] LLM features (not installed)")
            console.print("  [yellow]💡 Install: pip install google-generativeai[/yellow]")
            console.print("  [yellow]💡 Get API key: https://makersuite.google.com/app/apikey[/yellow]\n")


def _display_markdown(parsed: ParsedLog):
    """Display parsed log as Markdown"""
    md_lines = [
        f"# Log Analysis Report",
        f"",
        f"**Platform:** {parsed.platform}",
        f"**Job:** {parsed.job_name or 'Unknown'}",
        f"**Status:** {parsed.status}",
        f"**Build Number:** {parsed.build_number or 'N/A'}",
        f"",
        f"## Statistics",
        f"- Total Lines: {parsed.total_lines}",
        f"- Errors: {parsed.error_count}",
        f"- Warnings: {parsed.warning_count}",
        f"- Retries: {parsed.retry_count}",
        f"- Stages: {len(parsed.stages)}",
        f"",
    ]
    
    if parsed.stages:
        md_lines.append("## Stages")
        for stage in parsed.stages:
            md_lines.append(f"- **{stage.name}**: {stage.status}")
    
    if parsed.errors:
        md_lines.append("\n## Top Errors")
        for error in parsed.errors[:5]:
            md_lines.append(f"- Line {error.line_number}: {error.message}")
    
    md_text = "\n".join(md_lines)
    console.print(Markdown(md_text))


# ============================================================================
# Phase 2 Helper Functions
# ============================================================================

def _run_llm_analysis(parsed: ParsedLog, log_content: str, model: str, no_cache: bool, show_full: bool):
    """Run AI-powered analysis on parsed log (using Google Gemini)"""
    import os
    
    if not LLM_AVAILABLE:
        console.print("\n[red]❌ LLM features not available[/red]")
        console.print("[yellow]Install: pip install google-generativeai[/yellow]\n")
        return
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("\n[red]❌ GEMINI_API_KEY not set![/red]")
        console.print("[yellow]Get free API key: https://makersuite.google.com/app/apikey[/yellow]")
        console.print("[yellow]Then: export GEMINI_API_KEY='your-key-here'[/yellow]\n")
        console.print("[cyan]💡 Gemini is FREE (15 req/min, 1500 req/day)[/cyan]")
        console.print("[cyan]   No setup, no downloads, just an API key![/cyan]\n")
        return
    
    console.print("\n" + "="*70)
    console.print("[bold cyan]🤖 Phase 2: AI-Powered Analysis (Google Gemini)[/bold cyan]")
    console.print("="*70 + "\n")
    
    try:
        # Initialize Gemini client (FREE!)
        client = GeminiClient(api_key=api_key, model=model)
        cache = CacheManager(enabled=not no_cache) if CACHE_AVAILABLE else None
        cache_key = log_content
        
        # 1. Summarize
        console.print("[yellow]⏳ Generating AI summary...[/yellow]")
        summarizer = LogSummarizer(client)
        
        cached = cache.get(cache_key, "summaries") if (cache and not no_cache) else None
        if cached:
            console.print("[green]✅ Using cached summary[/green]\n")
            summary = cached
        else:
            summary = summarizer.summarize(parsed)
            if cache and not no_cache:
                cache.set(cache_key, summary, "summaries")
            console.print("[green]✅ Generated[/green]\n")
        
        _display_ai_summary(summary, console)
        
        # 2. Explain errors (if requested)
        if parsed.errors and show_full:
            console.print("\n[yellow]⏳ Explaining errors...[/yellow]")
            explainer = ErrorExplainer(client)
            
            cached = cache.get(cache_key + "_explain", "explanations") if (cache and not no_cache) else None
            if cached:
                console.print("[green]✅ Using cached explanation[/green]\n")
                explanation = cached
            else:
                explanation = explainer.explain(parsed.errors[0], parsed)
                if cache and not no_cache:
                    cache.set(cache_key + "_explain", explanation, "explanations")
                console.print("[green]✅ Generated[/green]\n")
            
            _display_ai_explanation(explanation, console)
            
            # 3. Fix suggestions
            console.print("\n[yellow]⏳ Generating fix suggestions...[/yellow]")
            fixer = FixSuggester(client)
            
            cached = cache.get(cache_key + "_fix", "fixes") if (cache and not no_cache) else None
            if cached:
                console.print("[green]✅ Using cached fix[/green]\n")
                fix_plan = cached
            else:
                fix_plan = fixer.suggest_fix(parsed.errors[0], parsed)
                if cache and not no_cache:
                    cache.set(cache_key + "_fix", fix_plan, "fixes")
                console.print("[green]✅ Generated[/green]\n")
            
            _display_ai_fix(fix_plan, console)
        
        # Show stats
        info = client.get_model_info()
        
        console.print("\n" + "-"*70)
        console.print(f"[dim]🤖 Model: {info['model']} ({info['provider']})[/dim]")
        console.print(f"[dim]🎉 Free Tier: {info['rate_limit']}[/dim]")
        
        if cache:
            cache_stats = cache.get_stats()
            if cache_stats['total_requests'] > 0:
                console.print(f"[dim]💾 Cache Hit Rate: {cache_stats['hit_rate']:.1f}%[/dim]")
        
        console.print("-"*70)
        
    except Exception as e:
        console.print(f"\n[red]❌ LLM analysis failed: {e}[/red]")


def _display_ai_summary(summary, console):
    """Display AI summary"""
    console.print(Panel(
        f"[bold]STATUS:[/bold] {summary.status}\n\n"
        f"[bold]MAIN ISSUE:[/bold]\n{summary.main_issue}\n\n"
        f"[bold]KEY POINTS:[/bold]\n" +
        "\n".join(f"  • {point}" for point in summary.key_points) +
        f"\n\n[bold]IMPACT:[/bold] {summary.impact}\n"
        f"[bold]CONFIDENCE:[/bold] {summary.confidence}%",
        title="🤖 AI Summary",
        border_style="cyan",
    ))


def _display_ai_explanation(explanation, console):
    """Display error explanation"""
    console.print(Panel(
        f"[bold]ROOT CAUSE:[/bold]\n{explanation.root_cause}\n\n"
        f"[bold]COMMON SCENARIOS:[/bold]\n" +
        "\n".join(f"  • {s}" for s in explanation.common_scenarios[:3]) +
        f"\n\n[bold]TECHNICAL DETAILS:[/bold]\n{explanation.technical_details}\n\n"
        f"[bold]CONFIDENCE:[/bold] {explanation.confidence}%",
        title="🔍 Error Explanation",
        border_style="yellow",
    ))


def _display_ai_fix(fix_plan, console):
    """Display fix suggestions"""
    text = f"[bold]DIAGNOSIS:[/bold]\n{fix_plan.diagnosis}\n\n"
    
    if fix_plan.quick_fix:
        text += f"[bold]QUICK FIX:[/bold]\n[green]{fix_plan.quick_fix}[/green]\n\n"
    
    text += "[bold]STEPS:[/bold]\n"
    for i, step in enumerate(fix_plan.detailed_steps[:5], 1):
        text += f"  {i}. {step}\n"
    
    if fix_plan.prevention_tips:
        text += "\n[bold]PREVENTION:[/bold]\n"
        text += "\n".join(f"  • {tip}" for tip in fix_plan.prevention_tips[:3])
    
    text += f"\n\n[bold]CONFIDENCE:[/bold] {fix_plan.confidence}%"
    
    console.print(Panel(text, title="💡 Fix Suggestions", border_style="green"))


def main():
    """Entry point for the CLI"""
    app()


if __name__ == "__main__":
    main()
