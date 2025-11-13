#!/usr/bin/env python3
"""
Analytics Dashboard - View feedback statistics and insights

This script provides analytics on user feedback to help improve the model.
"""

import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
import typer

from src.feedback.manager import FeedbackManager

console = Console()
app = typer.Typer()


def create_stats_panel(stats: dict) -> Panel:
    """Create formatted panel with overall statistics"""
    content = f"""
[bold]Period:[/bold] Last {stats['period_days']} days
[bold]Total Feedback:[/bold] {stats['total_feedback']}
[bold]Average Rating:[/bold] {stats['avg_rating']:.2f}/5.0 ⭐
[bold]Model Accuracy:[/bold] {stats['accuracy']:.1f}%
[bold]Corrections Needed:[/bold] {stats['corrections_needed']}
[bold]Average Confidence:[/bold] {stats['avg_confidence']:.1f}%
    """.strip()
    
    return Panel(content, title="📊 Overall Statistics", border_style="cyan")


def create_category_table(category_dist: dict) -> Table:
    """Create table showing error category distribution"""
    table = Table(title="🏷️  Error Category Distribution", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")
    
    total = sum(category_dist.values())
    
    # Sort by count descending
    sorted_categories = sorted(category_dist.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories:
        percentage = (count / total * 100) if total > 0 else 0
        table.add_row(category, str(count), f"{percentage:.1f}%")
    
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{total}[/bold]", "[bold]100.0%[/bold]")
    
    return table


def create_mode_table(mode_usage: dict) -> Table:
    """Create table showing analysis mode usage"""
    table = Table(title="🎯 Analysis Mode Usage", show_header=True)
    table.add_column("Mode", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")
    
    total = sum(mode_usage.values())
    
    # Sort by count descending
    sorted_modes = sorted(mode_usage.items(), key=lambda x: x[1], reverse=True)
    
    for mode, count in sorted_modes:
        percentage = (count / total * 100) if total > 0 else 0
        table.add_row(mode, str(count), f"{percentage:.1f}%")
    
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{total}[/bold]", "[bold]100.0%[/bold]")
    
    return table


def create_retraining_table(history: list) -> Table:
    """Create table showing model retraining history"""
    table = Table(title="🔄 Model Retraining History", show_header=True)
    table.add_column("Date", style="cyan")
    table.add_column("Samples", justify="right", style="magenta")
    table.add_column("Feedback", justify="right", style="yellow")
    table.add_column("Old Acc", justify="right", style="red")
    table.add_column("New Acc", justify="right", style="green")
    table.add_column("Improvement", justify="right", style="blue")
    
    for record in history:
        old_acc = record['old_accuracy']
        new_acc = record['new_accuracy']
        improvement = new_acc - old_acc
        
        date_str = record['retrain_timestamp'][:10]  # YYYY-MM-DD
        
        table.add_row(
            date_str,
            str(record['num_training_samples']),
            str(record['num_feedback_samples']),
            f"{old_acc:.1f}%",
            f"{new_acc:.1f}%",
            f"+{improvement:.1f}%" if improvement >= 0 else f"{improvement:.1f}%"
        )
    
    return table


@app.command()
def stats(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to include"),
    show_retraining: bool = typer.Option(False, "--retraining", "-r", help="Show retraining history"),
):
    """
    Display feedback statistics and analytics.
    
    Shows:
    - Overall statistics (total feedback, avg rating, accuracy)
    - Error category distribution
    - Analysis mode usage
    - Model retraining history (with --retraining flag)
    """
    console.print("\n")
    console.print("="*70)
    console.print("[bold cyan]📊 AI-LogGuard Analytics Dashboard[/bold cyan]")
    console.print("="*70)
    console.print("\n")
    
    try:
        manager = FeedbackManager()
        
        # Get statistics
        stats_data = manager.get_feedback_stats(days=days)
        
        # Display overall stats
        console.print(create_stats_panel(stats_data))
        console.print()
        
        # Display category distribution
        if stats_data['category_distribution']:
            console.print(create_category_table(stats_data['category_distribution']))
            console.print()
        else:
            console.print("[yellow]No category data available yet[/yellow]\n")
        
        # Display mode usage
        if stats_data['mode_usage']:
            console.print(create_mode_table(stats_data['mode_usage']))
            console.print()
        else:
            console.print("[yellow]No mode usage data available yet[/yellow]\n")
        
        # Display retraining history
        if show_retraining:
            history = manager.get_retraining_history(limit=10)
            if history:
                console.print(create_retraining_table(history))
                console.print()
            else:
                console.print("[yellow]No retraining history yet[/yellow]\n")
        
        # Recommendations
        console.print(Panel(
            _get_recommendations(stats_data),
            title="💡 Recommendations",
            border_style="yellow"
        ))
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def _get_recommendations(stats: dict) -> str:
    """Generate recommendations based on statistics"""
    recommendations = []
    
    # Check feedback volume
    if stats['total_feedback'] < 10:
        recommendations.append("• Collect more feedback to improve model accuracy")
    
    # Check accuracy
    if stats['accuracy'] < 80:
        recommendations.append(f"• Model accuracy is {stats['accuracy']:.1f}% - consider retraining with corrected samples")
    elif stats['accuracy'] > 95:
        recommendations.append(f"• Excellent accuracy ({stats['accuracy']:.1f}%)! Model is performing well")
    
    # Check corrections needed
    if stats['corrections_needed'] > 5:
        recommendations.append(f"• {stats['corrections_needed']} predictions need correction - use for retraining")
    
    # Check confidence
    if stats['avg_confidence'] < 70:
        recommendations.append(f"• Average confidence is low ({stats['avg_confidence']:.1f}%) - model may need more training data")
    
    # Check rating
    if stats['avg_rating'] < 3.0 and stats['total_feedback'] > 5:
        recommendations.append(f"• User satisfaction is low ({stats['avg_rating']:.1f}/5.0) - review analysis quality")
    elif stats['avg_rating'] >= 4.0:
        recommendations.append(f"• Great user satisfaction ({stats['avg_rating']:.1f}/5.0)! Keep it up")
    
    if not recommendations:
        recommendations.append("• Everything looks good! Continue collecting feedback")
    
    return "\n".join(recommendations)


@app.command()
def export(
    output: str = typer.Option(
        "data/feedback_export.json",
        "--output",
        "-o",
        help="Output file path"
    ),
    incorrect_only: bool = typer.Option(
        False,
        "--incorrect-only",
        "-i",
        help="Only export user-corrected samples"
    ),
):
    """
    Export feedback data for model retraining.
    
    Exports feedback to JSON file with:
    - Log content
    - Correct label (user-corrected or ML prediction)
    - Platform metadata
    """
    try:
        manager = FeedbackManager()
        
        console.print(f"\n[yellow]📦 Exporting feedback data...[/yellow]")
        
        count = manager.export_training_data(
            output_path=output,
            include_incorrect_only=incorrect_only
        )
        
        console.print(f"[green]✅ Exported {count} samples to: {output}[/green]")
        
        if incorrect_only:
            console.print("[dim]   (Only user-corrected samples)[/dim]")
        else:
            console.print("[dim]   (All feedback samples)[/dim]")
        
        console.print()
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")


@app.command()
def low_confidence(
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Confidence threshold"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum samples to show"),
):
    """
    Show samples where ML had low confidence (needs human review).
    """
    try:
        manager = FeedbackManager()
        samples = manager.get_low_confidence_samples(threshold=threshold, limit=limit)
        
        if not samples:
            console.print(f"\n[green]✅ No low-confidence samples found below {threshold:.0%}[/green]\n")
            return
        
        console.print(f"\n[yellow]⚠️  Found {len(samples)} samples with confidence < {threshold:.0%}[/yellow]\n")
        
        table = Table(title=f"Low Confidence Samples (< {threshold:.0%})", show_header=True)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Log File", style="magenta", width=30)
        table.add_column("Prediction", style="yellow", width=20)
        table.add_column("Confidence", justify="right", style="red", width=12)
        table.add_column("Status", style="green", width=10)
        
        for sample in samples:
            status = "✅ Reviewed" if sample['is_correct'] is not None else "⏳ Pending"
            conf_pct = f"{sample['ml_confidence']:.1%}"
            
            table.add_row(
                str(sample['id']),
                sample['log_file'] or "N/A",
                sample['ml_predicted_category'],
                conf_pct,
                status
            )
        
        console.print(table)
        console.print()
        console.print("[dim]💡 Review these samples to improve model accuracy[/dim]\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")


if __name__ == '__main__':
    app()
