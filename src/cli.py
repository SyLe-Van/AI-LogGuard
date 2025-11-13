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

# Phase 3: Hybrid ML+LLM imports (conditional)
try:
    from .hybrid.analyzer import HybridAnalyzer
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False
    HybridAnalyzer = None

# Cache manager (optional, can work without it)
try:
    from .cache.cache_manager import CacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    CacheManager = None

# Phase 4: Feedback & Learning imports (conditional)
try:
    from .feedback.manager import FeedbackManager
    FEEDBACK_AVAILABLE = True
except ImportError:
    FEEDBACK_AVAILABLE = False
    FeedbackManager = None

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
    mode: str = typer.Option(
        "hybrid",
        "--mode",
        "-m",
        help="[Phase 3] Analysis mode: hybrid (ML+LLM), ml-only (fast), llm-only (original)",
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
    Phase 3 (--mode):  Hybrid ML+LLM for better accuracy & cost efficiency
    
    \b
    Modes:
      hybrid (default): ML classification → specialized LLM prompts (30-50% cost reduction)
      ml-only:          Fast ML-only classification (no LLM, instant results)
      llm-only:         Original LLM-only analysis (highest quality)
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
    
    # Phase 2/3: AI-powered analysis
    if use_llm:
        # Use hybrid analyzer if available and mode is hybrid/ml-only
        if HYBRID_AVAILABLE and mode in ("hybrid", "ml-only"):
            _run_hybrid_analysis(parsed, log_content, model, no_cache, mode, show_full)
        else:
            # Fallback to original LLM analysis (llm-only mode)
            _run_llm_analysis(parsed, log_content, model, no_cache, show_full)
    elif parsed.status == BuildStatus.FAILED and parsed.error_count > 0:
        console.print(f"\n[yellow]💡 Tip: Add --llm --mode hybrid for fast ML+AI analysis[/yellow]")
    
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
    analyze: bool = typer.Option(
        False,
        "--analyze",
        "-a",
        help="Analyze logs immediately after fetching",
    ),
    llm: bool = typer.Option(
        False,
        "--llm",
        help="Use LLM for analysis (requires --analyze)",
    ),
    mode: Optional[str] = typer.Option(
        None,
        "--mode",
        help="Analysis mode: ml-only, llm-only, hybrid, hybrid-always (requires --analyze)",
    ),
):
    """
    📥 Fetch logs directly from CI/CD platform
    
    Fetch logs from Jenkins, GitHub Actions, etc. and optionally save to file.
    Add --analyze flag to automatically analyze after fetching.
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
    
    # Analyze immediately if requested
    if analyze:
        console.print(f"\n[bold green]🔍 Analyzing fetched logs...[/bold green]\n")
        
        # Create temporary file if not saving
        if not save_to:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8')
            temp_file.write(logs)
            temp_file.close()
            log_file_path = Path(temp_file.name)
        else:
            log_file_path = save_to
        
        # Parse and analyze
        try:
            from .parsers import parse_log
            
            # Parse logs
            with console.status("⏳ Parsing logs..."):
                parsed = parse_log(logs, job_name=job_id)
            
            console.print("✅ Log parsed successfully\n")
            
            # Display parsed results
            display_parsed_log(parsed, console=console, show_full=False)
            
            # Run LLM/Hybrid analysis if requested
            if llm:
                if HYBRID_AVAILABLE and mode in ("hybrid", "ml-only"):
                    _run_hybrid_analysis(parsed, logs, model="gemini-2.5-flash", 
                                       no_cache=False, mode=mode or "hybrid", show_full=False)
                else:
                    _run_llm_analysis(parsed, logs, model="gemini-2.5-flash",
                                    no_cache=False, show_full=False)
            
            # Clean up temp file
            if not save_to:
                import os
                os.unlink(log_file_path)
                
        except Exception as e:
            console.print(f"[red]❌ Analysis error: {e}[/red]")
            import traceback
            traceback.print_exc()
    else:
        # Display preview only
        if not save_to:
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

def _run_hybrid_analysis(parsed: ParsedLog, log_content: str, model: str, no_cache: bool, mode: str, show_full: bool):
    """Run hybrid ML+LLM analysis on parsed log (Phase 3)"""
    import os
    
    if not HYBRID_AVAILABLE:
        console.print("\n[yellow]⚠️  Hybrid mode not available, falling back to LLM-only[/yellow]")
        _run_llm_analysis(parsed, log_content, model, no_cache, show_full)
        return
    
    # Check for API key only if mode requires LLM
    api_key = os.getenv("GEMINI_API_KEY")
    
    if mode != "ml-only" and not api_key:
        console.print("\n[red]❌ GEMINI_API_KEY not set![/red]")
        console.print("[yellow]Get free API key: https://makersuite.google.com/app/apikey[/yellow]")
        console.print("[yellow]Then: export GEMINI_API_KEY='your-key-here'[/yellow]\n")
        console.print("[cyan]💡 Or use --mode ml-only for ML classification without LLM[/cyan]\n")
        return
    
    console.print("\n" + "="*70)
    if mode == "ml-only":
        console.print("[bold magenta]🚀 Phase 3: ML-Only Classification (No LLM)[/bold magenta]")
    else:
        console.print("[bold magenta]🚀 Phase 3: Hybrid ML+LLM Analysis[/bold magenta]")
    console.print("="*70 + "\n")
    
    try:
        # Initialize hybrid analyzer
        if mode == "ml-only":
            analyzer = HybridAnalyzer(api_key=None)
        else:
            analyzer = HybridAnalyzer(api_key=api_key)
        
        # Run analysis
        console.print(f"[yellow]⏳ Running {mode} analysis...[/yellow]")
        result = analyzer.analyze(parsed, mode=mode)
        console.print("[green]✅ Analysis complete[/green]\n")
        
        # Display results
        _display_hybrid_result(result, console, show_full)
        
        return result
        
    except Exception as e:
        console.print(f"\n[red]❌ Hybrid analysis failed: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return None
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def _display_hybrid_result(result: dict, console, show_full: bool):
    """Display hybrid analysis result"""
    
    # ✅ Root Cause Detection (if available)
    if 'root_cause' in result and result['root_cause']:
        from src.utils.root_cause import root_cause_detector
        root_cause_text = root_cause_detector.format_root_cause(result['root_cause'])
        
        console.print(Panel(
            root_cause_text,
            title="🎯 Root Cause Detection",
            border_style="red bold",
        ))
        console.print()
    
    # ML Prediction
    ml_panel_text = (
        f"[bold]Error Type:[/bold] {result['error_type']}\n"
        f"[bold]Confidence:[/bold] {result['confidence']:.1%}\n"
        f"[bold]Strategy:[/bold] {result.get('strategy', result['mode'])}"
    )
    
    # Add root cause override info if present
    if 'root_cause_override' in result:
        ml_panel_text += f"\n[dim italic]{result['root_cause_override']}[/dim italic]"
    
    console.print(Panel(
        ml_panel_text,
        title="🎯 ML Classification",
        border_style="blue",
    ))
    
    # LLM Explanation (if available)
    if 'explanation' in result and result['explanation']:
        console.print()
        
        # Determine panel style based on strategy
        strategy = result.get('strategy', '')
        if 'ML Analysis' in strategy or 'fallback' in strategy.lower():
            title = "🤖 ML-Based Analysis"
            style = "yellow"
        else:
            title = "🤖 AI Analysis (Gemini)"
            style = "cyan"
        
        console.print(Panel(
            result['explanation'],
            title=title,
            border_style=style,
        ))
        
        # Show any warnings/notes
        if 'error' in result and result['error']:
            error_msg = result['error']
            
            # Simplify error messages for better UX
            if "safety filters" in error_msg.lower():
                note_msg = "⚠️  Gemini AI blocked this log content (safety filters). Using ML-based analysis instead (still accurate!)."
            elif "quota" in error_msg.lower() or "429" in error_msg:
                note_msg = "⚠️  Gemini API quota limit reached. Using ML-based analysis instead (still accurate!)."
            else:
                note_msg = error_msg
            
            console.print(f"\n[dim yellow]ℹ️  Note: {note_msg}[/dim yellow]")
    
    # Show probabilities (if full)
    if show_full and 'ml_prediction' in result and result['ml_prediction']:
        ml_pred = result['ml_prediction']
        if 'proba' in ml_pred:
            console.print("\n[bold]Probability Distribution:[/bold]")
            
            # Get label encoder to map indices to class names
            from src.ml.predictor import ErrorClassifier
            clf = ErrorClassifier()
            classes = clf.label_encoder.classes_
            
            # Create table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Error Type", style="cyan")
            table.add_column("Probability", justify="right")
            table.add_column("Bar", style="green")
            
            for i, prob in enumerate(ml_pred['proba']):
                if prob > 0.01:  # Only show >1%
                    bar = "█" * int(prob * 50)
                    table.add_row(classes[i], f"{prob:.1%}", bar)
            
            console.print(table)
    
    # Cost info
    if 'cost_estimate' in result:
        cost = result['cost_estimate']
        tokens = result.get('tokens_used', 0)
        if tokens > 0:
            console.print(f"\n[dim]💰 Tokens: {tokens} | Cost: ${cost:.4f} (FREE tier)[/dim]")
    
    # ✅ FINAL ONE-LINER VERDICT (concise summary)
    if 'root_cause' in result and result['root_cause']:
        rc = result['root_cause']
        console.print("\n" + "="*80)
        console.print("[bold magenta]📌 QUICK SUMMARY[/bold magenta]")
        console.print("="*80)
        
        # Root cause
        severity_emoji = "🔴" if rc['severity'] == 'FATAL' else "🟡" if rc['severity'] == 'HIGH' else "🟢"
        console.print(f"{severity_emoji} [bold]Root Cause:[/bold] {rc['root_cause']} ([red]{rc['severity']}[/red])")
        
        # Error line
        console.print(f"📍 [bold]Error:[/bold] {rc['line_content'][:100]}...")
        
        # Failed stage
        if rc.get('stage'):
            stage_name = rc['stage']
            # Add emoji based on stage name
            stage_emoji = "🐳" if 'docker' in stage_name.lower() else "🏗️" if 'build' in stage_name.lower() else "🚀" if 'deploy' in stage_name.lower() else "🎯"
            console.print(f"{stage_emoji} [bold]Failed Stage:[/bold] {stage_name}")
        
        console.print("="*80 + "\n")


def _collect_feedback(result: dict, log_content: str, mode: str, parsed: ParsedLog):
    """
    Collect user feedback on analysis result (Phase 4).
    
    Args:
        result: Analysis result dict
        log_content: Original log text
        mode: Analysis mode used
        parsed: Parsed log object
    """
    if not FEEDBACK_AVAILABLE:
        return
    
    console.print("\n" + "="*70)
    console.print("[bold cyan]📊 Help us improve! Quick feedback (optional)[/bold cyan]")
    console.print("="*70)
    
    # Ask for feedback
    try:
        # Quick rating
        console.print("\n[bold]Was this analysis helpful?[/bold]")
        console.print("  1 - Not helpful at all")
        console.print("  2 - Somewhat helpful")
        console.print("  3 - Moderately helpful")
        console.print("  4 - Very helpful")
        console.print("  5 - Extremely helpful")
        console.print("  [dim](Press Enter to skip)[/dim]")
        
        rating_input = typer.prompt("Rating (1-5)", default="", show_default=False)
        rating = int(rating_input) if rating_input and rating_input.isdigit() else None
        
        # Check if prediction was correct
        console.print(f"\n[bold]ML predicted:[/bold] [yellow]{result['error_type']}[/yellow]")
        console.print("[bold]Is this correct?[/bold]")
        console.print("  y - Yes, correct")
        console.print("  n - No, incorrect")
        console.print("  [dim](Press Enter to skip)[/dim]")
        
        correct_input = typer.prompt("Correct? (y/n)", default="", show_default=False).lower()
        
        is_correct = None
        correct_category = None
        
        if correct_input == 'y':
            is_correct = True
        elif correct_input == 'n':
            is_correct = False
            
            # Ask for correct category
            console.print("\n[bold]What is the correct error type?[/bold]")
            error_types = [
                "dependency_error",
                "syntax_error",
                "test_failure",
                "timeout",
                "environment_error",
                "network_error",
                "permission_error"
            ]
            for i, cat in enumerate(error_types, 1):
                console.print(f"  {i} - {cat}")
            
            cat_input = typer.prompt("Select correct type (1-7)", default="", show_default=False)
            if cat_input.isdigit() and 1 <= int(cat_input) <= 7:
                correct_category = error_types[int(cat_input) - 1]
        
        # Optional comments
        console.print("\n[bold]Any additional comments? (optional)[/bold]")
        console.print("[dim](Press Enter to skip)[/dim]")
        comments = typer.prompt("Comments", default="", show_default=False)
        
        # Save feedback
        if rating or is_correct is not None or comments:
            feedback_manager = FeedbackManager()
            
            ml_prediction = {
                'error_type': result['error_type'],
                'confidence': result['confidence'],
                'probabilities': result.get('probabilities', {})
            }
            
            feedback_id = feedback_manager.save_feedback(
                log_content=log_content,
                ml_prediction=ml_prediction,
                analysis_mode=mode,
                user_rating=rating,
                is_correct=is_correct,
                correct_category=correct_category,
                user_comments=comments or None,
                platform=str(parsed.platform) if hasattr(parsed, 'platform') else None,
                llm_explanation=result.get('explanation'),
                llm_tokens=result.get('tokens_used'),
            )
            
            console.print(f"\n[green]✅ Thank you! Feedback saved (ID: {feedback_id})[/green]")
            console.print("[dim]Your feedback helps improve the model![/dim]")
        else:
            console.print("\n[dim]⏭️  Skipped feedback[/dim]")
    
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]⏭️  Feedback cancelled[/dim]")
    except Exception as e:
        console.print(f"\n[yellow]⚠️  Could not save feedback: {e}[/yellow]")


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
