"""
Display utilities for Rich console output
Beautiful formatting for log analysis results
"""
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from ..models import ParsedLog, BuildStatus, LogLevel, StageInfo


def display_parsed_log(
    parsed: ParsedLog,
    console: Optional[Console] = None,
    show_full: bool = False
):
    """
    Display full parsed log analysis with rich formatting
    
    Args:
        parsed: ParsedLog object to display
        console: Rich Console instance (creates new one if None)
        show_full: Show all errors/warnings vs top 10
    """
    if console is None:
        console = Console()
    
    # Header
    _display_header(parsed, console)
    
    # Statistics
    _display_statistics(parsed, console)
    
    # Stages
    if parsed.stages:
        _display_stages(parsed.stages, console)
    
    # Errors
    if parsed.errors:
        _display_errors(parsed.errors, console, show_all=show_full)
    
    # Warnings
    if parsed.warnings:
        _display_warnings(parsed.warnings, console, show_all=show_full)
    
    # Final verdict
    _display_verdict(parsed, console)


def display_summary(parsed: ParsedLog, console: Optional[Console] = None):
    """
    Display quick summary of parsed log
    
    Args:
        parsed: ParsedLog object
        console: Rich Console instance
    """
    if console is None:
        console = Console()
    
    summary = parsed.get_summary()
    
    # Determine actual status based on errors
    actual_status = summary['status']
    if summary['errors'] > 0 and actual_status == BuildStatus.SUCCESS:
        actual_status = BuildStatus.UNSTABLE
    
    # Create summary table
    table = Table(title="📊 Log Summary", show_header=False, box=None)
    table.add_column("Key", style="cyan bold")
    table.add_column("Value")
    
    # Platform icon
    platform_icon = {
        "jenkins": "🔧",
        "github-actions": "🐙",
        "gitlab-ci": "🦊",
    }.get(summary['platform'], "❓")
    
    table.add_row("Platform", f"{platform_icon} {summary['platform']}")
    table.add_row("Job Name", summary['job_name'] or "Unknown")
    table.add_row("Build Number", summary['build_number'] or "N/A")
    
    # Status with color
    status_text = _get_status_text(actual_status)
    table.add_row("Status", status_text)
    
    if summary['duration']:
        duration_text = f"{summary['duration']:.1f}s"
        table.add_row("Duration", duration_text)
    
    table.add_row("Stages", str(summary['stages']))
    
    # Error/Warning counts with color
    error_text = f"[red bold]{summary['errors']}[/red bold]" if summary['errors'] > 0 else f"[green]{summary['errors']}[/green]"
    warning_text = f"[yellow bold]{summary['warnings']}[/yellow bold]" if summary['warnings'] > 0 else f"[green]{summary['warnings']}[/green]"
    
    table.add_row("Errors", error_text)
    table.add_row("Warnings", warning_text)
    
    if summary['retries'] > 0:
        table.add_row("Retries", f"[yellow]{summary['retries']}[/yellow]")
    
    console.print(table)


def _display_header(parsed: ParsedLog, console: Console):
    """Display header with job information"""
    # Determine actual build status based on errors/warnings
    actual_status = parsed.status
    if parsed.error_count > 0 and parsed.status == BuildStatus.SUCCESS:
        actual_status = BuildStatus.UNSTABLE
    
    status_text = _get_status_text(actual_status)
    platform_icon = {
        "jenkins": "🔧",
        "github-actions": "🐙",
        "gitlab-ci": "🦊",
    }.get(str(parsed.platform).lower(), "❓")
    
    title = f"{platform_icon} {str(parsed.platform).upper()} - {parsed.job_name or 'Unknown Job'}"
    
    info_lines = [
        f"Build: {parsed.build_number or 'N/A'}",
        f"Status: {status_text}",
    ]
    
    if parsed.duration_seconds:
        info_lines.append(f"Duration: {parsed.duration_seconds:.1f}s")
    
    if parsed.triggered_by:
        info_lines.append(f"Triggered by: {parsed.triggered_by}")
    
    panel = Panel(
        "\n".join(info_lines),
        title=title,
        border_style="blue",
    )
    console.print(panel)
    console.print()


def _display_statistics(parsed: ParsedLog, console: Console):
    """Display statistics table"""
    table = Table(title="📊 Statistics", show_header=True)
    
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")
    
    table.add_row("Total Lines", str(parsed.total_lines))
    table.add_row("Stages/Steps", str(len(parsed.stages)))
    
    # Errors with color
    error_style = "red bold" if parsed.error_count > 0 else "green"
    table.add_row("Errors", f"[{error_style}]{parsed.error_count}[/{error_style}]")
    
    # Warnings with color
    warning_style = "yellow" if parsed.warning_count > 0 else "green"
    table.add_row("Warnings", f"[{warning_style}]{parsed.warning_count}[/{warning_style}]")
    
    if parsed.retry_count > 0:
        table.add_row("Retries", f"[yellow]{parsed.retry_count}[/yellow]")
    
    console.print(table)
    console.print()


def _display_stages(stages: list, console: Console):
    """Display stages/steps tree"""
    tree = Tree("🎯 Stages/Steps")
    
    for stage in stages:
        # Get status value properly - handle both string and enum
        if hasattr(stage.status, 'value'):
            stage_status = stage.status.value
        elif isinstance(stage.status, str):
            stage_status = stage.status
        else:
            stage_status = str(stage.status).split('.')[-1]  # Extract enum name
        
        status_icon = {
            "SUCCESS": "✅",
            "FAILED": "❌",
            "UNSTABLE": "⚠️",
            "UNKNOWN": "❓",
        }.get(stage_status.upper() if isinstance(stage_status, str) else stage_status, "❓")
        
        stage_label = f"{status_icon} {stage.name} - [bold]{stage_status}[/bold]"
        
        # Add details if there are errors/warnings
        details = []
        if stage.error_count > 0:
            details.append(f"[red]{stage.error_count} errors[/red]")
        if stage.warning_count > 0:
            details.append(f"[yellow]{stage.warning_count} warnings[/yellow]")
        if stage.retry_count > 0:
            details.append(f"[blue]{stage.retry_count} retries[/blue]")
        
        if details:
            stage_label += f" ({', '.join(details)})"
        
        tree.add(stage_label)
    
    console.print(tree)
    console.print()


def _display_errors(errors: list, console: Console, show_all: bool = False):
    """Display errors table"""
    display_count = len(errors) if show_all else min(10, len(errors))
    
    title = f"❌ Errors (showing {display_count} of {len(errors)})"
    table = Table(title=title, show_header=True)
    
    table.add_column("Line", style="dim", width=8, justify="right")
    table.add_column("Level", width=12)
    table.add_column("Message", style="red", no_wrap=False)
    
    for error in errors[:display_count]:
        # Get level value properly - handle both string and enum
        if hasattr(error.level, 'value'):
            level_value = error.level.value
        elif isinstance(error.level, str):
            level_value = error.level
        else:
            level_value = str(error.level).split('.')[-1]  # Extract enum name
        
        level_style = "red bold" if level_value == "CRITICAL" else "red"
        
        table.add_row(
            str(error.line_number),
            f"[{level_style}]{level_value}[/{level_style}]",
            error.message[:120]  # Truncate very long messages
        )
    
    console.print(table)
    console.print()


def _display_warnings(warnings: list, console: Console, show_all: bool = False):
    """Display warnings table"""
    display_count = len(warnings) if show_all else min(10, len(warnings))
    
    title = f"⚠️ Warnings (showing {display_count} of {len(warnings)})"
    table = Table(title=title, show_header=True)
    
    table.add_column("Line", style="dim", width=6)
    table.add_column("Message", style="yellow")
    
    for warning in warnings[:display_count]:
        table.add_row(
            str(warning.line_number),
            warning.message[:100]
        )
    
    console.print(table)
    console.print()


def _get_status_text(status: str) -> str:
    """Get colored status text"""
    status_map = {
        BuildStatus.SUCCESS: "[green bold]✅ SUCCESS[/green bold]",
        BuildStatus.FAILED: "[red bold]❌ FAILED[/red bold]",
        BuildStatus.UNSTABLE: "[yellow bold]⚠️ UNSTABLE[/yellow bold]",
        BuildStatus.TIMEOUT: "[red]⏱️ TIMEOUT[/red]",
        BuildStatus.ABORTED: "[dim]🛑 ABORTED[/dim]",
        BuildStatus.UNKNOWN: "[dim]❓ UNKNOWN[/dim]",
    }
    
    return status_map.get(status, str(status))


def _display_verdict(parsed: ParsedLog, console: Console):
    """Display final verdict/recommendation"""
    # Determine severity
    has_errors = parsed.error_count > 0
    has_warnings = parsed.warning_count > 0
    
    if not has_errors and not has_warnings:
        verdict = Panel(
            "[green bold]✅ Build completed successfully![/green bold]\n"
            "[green]No errors or warnings detected. Safe to deploy.[/green]",
            title="📋 Final Verdict",
            border_style="green",
        )
    elif has_errors:
        verdict_text = f"[red bold]❌ Build has {parsed.error_count} error(s)[/red bold]"
        if has_warnings:
            verdict_text += f" [yellow]and {parsed.warning_count} warning(s)[/yellow]"
        verdict_text += "\n[red]Action required before deployment.[/red]"
        
        # Add failed stages info
        if parsed.stages:
            failed_stages = [s for s in parsed.stages if str(s.status) == "FAILED" or (hasattr(s.status, 'value') and s.status.value == "FAILED")]
            if failed_stages:
                verdict_text += f"\n[dim]Failed stages: {', '.join(s.name for s in failed_stages)}[/dim]"
        
        verdict = Panel(
            verdict_text,
            title="📋 Final Verdict",
            border_style="red",
        )
    else:  # Only warnings
        verdict = Panel(
            f"[yellow bold]⚠️ Build completed with {parsed.warning_count} warning(s)[/yellow bold]\n"
            "[yellow]Review warnings before production deployment.[/yellow]",
            title="📋 Final Verdict",
            border_style="yellow",
        )
    
    console.print(verdict)

