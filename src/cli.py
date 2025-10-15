"""
AI-LogGuard CLI - Modern CLI interface built with Typer
Main entry point for the application
"""
import sys
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
    ai: bool = typer.Option(
        False,
        "--ai",
        help="Enable AI-powered error explanation and fix suggestions (requires OpenAI API key)",
    ),
):
    """
    🔍 Analyze a CI/CD log file
    
    Parse and analyze logs from Jenkins, GitHub Actions, GitLab CI, etc.
    Use --ai flag to get AI-powered explanations and fix suggestions.
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
    
    # Output based on format
    if output_format == "json":
        console.print(json.dumps(parsed.dict(), indent=2, default=str))
    elif output_format == "markdown":
        _display_markdown(parsed)
    else:  # rich (default)
        display_parsed_log(parsed, console=console, show_full=show_full)
    
    # AI-powered analysis (if enabled)
    if ai and parsed.errors:
        _display_ai_analysis(parsed, console)
    
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
    ai: bool = typer.Option(
        False,
        "--ai",
        help="Use AI to generate intelligent summary (requires OpenAI API key)",
    ),
):
    """
    📊 Generate a quick summary of a log file
    
    Show high-level statistics and key information.
    Use --ai flag for intelligent AI-powered summary.
    """
    console.print(f"\n[bold blue]📊 Summarizing log file:[/bold blue] {log_file}\n")
    
    # Read and parse
    try:
        log_content = log_file.read_text(encoding='utf-8')
        parsed = parse_log(log_content, job_name=log_file.stem)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Display basic summary
    display_summary(parsed, console=console)
    
    # AI-powered summary (if enabled)
    if ai:
        _display_ai_summary(parsed, console)
    
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
def version():
    """Show version information"""
    console.print("\n[bold blue]AI-LogGuard[/bold blue] v0.1.0")
    console.print("AI-powered CI/CD log analysis tool\n")


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


def _display_ai_summary(parsed: ParsedLog, console: Console):
    """Display AI-powered summary"""
    from .llm import summarize_log
    
    console.print("\n[bold cyan]🤖 AI-Powered Summary[/bold cyan]")
    console.print("[dim]Generating intelligent summary...[/dim]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing with AI...", total=None)
        
        try:
            result = summarize_log(parsed, model="gpt-3.5-turbo")
            progress.update(task, description="✅ AI analysis complete")
        except Exception as e:
            console.print(f"[red]❌ AI analysis failed: {e}[/red]")
            console.print("[dim]Tip: Make sure you have set OPENAI_API_KEY in .env file[/dim]")
            return
    
    console.print()
    console.print(Panel(
        Markdown(result["summary"]),
        title="🤖 AI Summary",
        border_style="cyan"
    ))
    
    # Show usage statistics
    console.print(f"[dim]Tokens used: {result['tokens_used']} | "
                 f"Model: {result['model']} | "
                 f"Strategy: {result['strategy']}[/dim]\n")


def _display_ai_analysis(parsed: ParsedLog, console: Console):
    """Display AI-powered error analysis and fix suggestions"""
    from .llm import explain_error, suggest_fix
    
    console.print("\n[bold cyan]🤖 AI-Powered Error Analysis[/bold cyan]\n")
    
    # Limit to top 3 errors
    top_errors = parsed.errors[:3]
    
    for i, error in enumerate(top_errors, 1):
        console.print(f"[bold yellow]Error {i}/{len(top_errors)}[/bold yellow] (Line {error.line_number})")
        console.print(f"[red]{error.message}[/red]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Explain error
            task = progress.add_task(f"Analyzing error {i}...", total=None)
            
            try:
                explanation = explain_error(error, parsed)
                progress.update(task, description=f"✅ Error {i} explained")
            except Exception as e:
                console.print(f"[red]❌ Failed to explain error: {e}[/red]")
                continue
        
        console.print(Panel(
            Markdown(explanation["explanation"]),
            title=f"💡 Explanation - {explanation['error_category']}",
            border_style="blue"
        ))
        console.print()
        
        # Suggest fix
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Generating fix for error {i}...", total=None)
            
            try:
                fix_suggestion = suggest_fix(error, parsed)
                progress.update(task, description=f"✅ Fix generated for error {i}")
            except Exception as e:
                console.print(f"[red]❌ Failed to generate fix: {e}[/red]")
                continue
        
        console.print(Panel(
            Markdown(fix_suggestion["fix_suggestions"]),
            title="🔧 Fix Suggestions",
            border_style="green"
        ))
        
        console.print(f"[dim]Tokens used: {explanation['tokens_used'] + fix_suggestion['tokens_used']}[/dim]\n")
        
        if i < len(top_errors):
            console.print("[dim]" + "─" * 80 + "[/dim]\n")
    
    console.print("[dim]💡 Tip: Use --full flag to see all errors (showing top 3)[/dim]")


def main():
    """Entry point for the CLI"""
    app()


if __name__ == "__main__":
    main()
