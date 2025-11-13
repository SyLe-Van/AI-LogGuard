#!/usr/bin/env python3
"""
Model Retraining Pipeline

Retrain the error classifier with user-corrected feedback data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib
import json
from datetime import datetime
from typing import List, Dict, Any
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table

# ML imports
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from src.feedback.manager import FeedbackManager
from src.ml.predictor import ErrorClassifier

console = Console()
app = typer.Typer()


def load_original_training_data():
    """Load original training data"""
    # Load from models directory
    models_dir = Path(__file__).parent.parent / "models"
    
    X_train = joblib.load(models_dir / "X_train.pkl")
    y_train = joblib.load(models_dir / "y_train.pkl")
    X_test = joblib.load(models_dir / "X_test.pkl")
    y_test = joblib.load(models_dir / "y_test.pkl")
    
    return X_train, y_train, X_test, y_test


def prepare_feedback_samples(feedback_data: List[Dict[str, Any]], classifier: ErrorClassifier):
    """
    Convert feedback data to feature vectors.
    
    Args:
        feedback_data: List of feedback samples
        classifier: ErrorClassifier instance for feature extraction
    
    Returns:
        X_feedback: Feature matrix
        y_feedback: Labels
    """
    texts = []
    labels = []
    
    for sample in feedback_data:
        texts.append(sample['log_content'])
        labels.append(sample['label'])
    
    # Extract features using same pipeline as training
    X_feedback = []
    for text in texts:
        features = classifier.extract_features(text, platform="jenkins")  # Default platform
        X_feedback.append(features)
    
    # Encode labels
    y_feedback = classifier.label_encoder.transform(labels)
    
    return X_feedback, y_feedback


@app.command()
def retrain(
    min_feedback: int = typer.Option(10, "--min-feedback", help="Minimum feedback samples required"),
    use_incorrect_only: bool = typer.Option(False, "--incorrect-only", help="Only use corrected samples"),
    test_split: float = typer.Option(0.2, "--test-split", help="Test set proportion"),
    save_model: bool = typer.Option(True, "--save/--no-save", help="Save retrained model"),
):
    """
    Retrain the error classifier model with user feedback.
    
    This will:
    1. Load original training data
    2. Load user feedback data
    3. Combine and retrain Random Forest model
    4. Evaluate performance
    5. Save new model (if --save)
    """
    console.print("\n")
    console.print("="*70)
    console.print("[bold cyan]🔄 Model Retraining Pipeline[/bold cyan]")
    console.print("="*70)
    console.print("\n")
    
    try:
        # Step 1: Load feedback data
        console.print("[yellow]📦 Step 1: Loading feedback data...[/yellow]")
        manager = FeedbackManager()
        feedback_samples = manager.get_training_data(include_incorrect_only=use_incorrect_only)
        
        if len(feedback_samples) < min_feedback:
            console.print(f"[red]❌ Insufficient feedback samples![/red]")
            console.print(f"   Required: {min_feedback}, Available: {len(feedback_samples)}")
            console.print(f"   Collect more user feedback before retraining.\n")
            return
        
        console.print(f"[green]✅ Loaded {len(feedback_samples)} feedback samples[/green]")
        
        if use_incorrect_only:
            corrected = sum(1 for s in feedback_samples if s.get('is_corrected'))
            console.print(f"[dim]   ({corrected} user-corrected samples)[/dim]")
        
        console.print()
        
        # Step 2: Load original training data
        console.print("[yellow]📦 Step 2: Loading original training data...[/yellow]")
        X_train_orig, y_train_orig, X_test_orig, y_test_orig = load_original_training_data()
        console.print(f"[green]✅ Loaded original data[/green]")
        console.print(f"[dim]   Train: {len(X_train_orig)} samples[/dim]")
        console.print(f"[dim]   Test: {len(X_test_orig)} samples[/dim]")
        console.print()
        
        # Step 3: Prepare feedback features
        console.print("[yellow]🔧 Step 3: Extracting features from feedback...[/yellow]")
        classifier = ErrorClassifier()
        X_feedback, y_feedback = prepare_feedback_samples(feedback_samples, classifier)
        console.print(f"[green]✅ Features extracted[/green]")
        console.print(f"[dim]   Feature dimension: {len(X_feedback[0])}, Samples: {len(X_feedback)}[/dim]")
        console.print()
        
        # Step 4: Combine datasets
        console.print("[yellow]🔀 Step 4: Combining datasets...[/yellow]")
        import numpy as np
        X_combined = np.vstack([X_train_orig, X_feedback])
        y_combined = np.concatenate([y_train_orig, y_feedback])
        console.print(f"[green]✅ Combined training data[/green]")
        console.print(f"[dim]   Total samples: {len(X_combined)}[/dim]")
        console.print()
        
        # Step 5: Evaluate old model
        console.print("[yellow]📊 Step 5: Evaluating current model...[/yellow]")
        old_model = classifier.model
        y_pred_old = old_model.predict(X_test_orig)
        old_accuracy = accuracy_score(y_test_orig, y_pred_old) * 100
        console.print(f"[cyan]📈 Current Model Accuracy: {old_accuracy:.2f}%[/cyan]")
        console.print()
        
        # Step 6: Train new model
        console.print("[yellow]🤖 Step 6: Training new model...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Training Random Forest...", total=100)
            
            new_model = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            new_model.fit(X_combined, y_combined)
            progress.update(task, completed=100)
        
        console.print(f"[green]✅ Model trained successfully[/green]")
        console.print()
        
        # Step 7: Evaluate new model
        console.print("[yellow]📊 Step 7: Evaluating new model...[/yellow]")
        y_pred_new = new_model.predict(X_test_orig)
        new_accuracy = accuracy_score(y_test_orig, y_pred_new) * 100
        improvement = new_accuracy - old_accuracy
        
        console.print(f"[cyan]📈 New Model Accuracy: {new_accuracy:.2f}%[/cyan]")
        
        if improvement > 0:
            console.print(f"[green]🎉 Improvement: +{improvement:.2f}%[/green]")
        elif improvement < 0:
            console.print(f"[red]⚠️  Regression: {improvement:.2f}%[/red]")
        else:
            console.print(f"[yellow]➡️  No change[/yellow]")
        
        console.print()
        
        # Show detailed classification report
        console.print("[bold]Detailed Classification Report:[/bold]\n")
        class_names = classifier.label_encoder.classes_
        report = classification_report(
            y_test_orig,
            y_pred_new,
            target_names=class_names,
            output_dict=True
        )
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Precision", justify="right", style="green")
        table.add_column("Recall", justify="right", style="yellow")
        table.add_column("F1-Score", justify="right", style="blue")
        table.add_column("Support", justify="right", style="white")
        
        for category in class_names:
            if category in report:
                metrics = report[category]
                table.add_row(
                    category,
                    f"{metrics['precision']:.3f}",
                    f"{metrics['recall']:.3f}",
                    f"{metrics['f1-score']:.3f}",
                    str(int(metrics['support']))
                )
        
        console.print(table)
        console.print()
        
        # Step 8: Save model
        if save_model:
            console.print("[yellow]💾 Step 8: Saving new model...[/yellow]")
            
            models_dir = Path(__file__).parent.parent / "models"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup old model
            old_model_path = models_dir / "error_classifier_rf.pkl"
            backup_path = models_dir / f"error_classifier_rf_backup_{timestamp}.pkl"
            
            if old_model_path.exists():
                import shutil
                shutil.copy(old_model_path, backup_path)
                console.print(f"[dim]   Backed up old model to: {backup_path.name}[/dim]")
            
            # Save new model
            new_model_path = models_dir / "error_classifier_rf.pkl"
            joblib.dump(new_model, new_model_path)
            console.print(f"[green]✅ New model saved to: {new_model_path}[/green]")
            
            # Update metadata
            metadata = {
                'model_type': 'RandomForestClassifier',
                'best_model': 'RandomForest',
                'accuracy': new_accuracy / 100,
                'training_samples': len(X_combined),
                'feedback_samples': len(feedback_samples),
                'retrained_at': datetime.now().isoformat(),
                'improvement': improvement,
            }
            joblib.dump(metadata, models_dir / "model_metadata.pkl")
            console.print(f"[dim]   Updated metadata[/dim]")
            console.print()
            
            # Log retraining event
            manager.log_retraining(
                num_training_samples=len(X_combined),
                num_feedback_samples=len(feedback_samples),
                old_accuracy=old_accuracy,
                new_accuracy=new_accuracy,
                model_path=str(new_model_path),
                notes=f"Retrained with {len(feedback_samples)} feedback samples"
            )
        
        # Summary
        console.print(Panel(
            f"""
[bold green]✅ Retraining Complete![/bold green]

[bold]Training Data:[/bold]
  • Original: {len(X_train_orig)} samples
  • Feedback: {len(feedback_samples)} samples
  • Total: {len(X_combined)} samples

[bold]Performance:[/bold]
  • Old Accuracy: {old_accuracy:.2f}%
  • New Accuracy: {new_accuracy:.2f}%
  • Improvement: {improvement:+.2f}%

[bold]Next Steps:[/bold]
  • Test new model: python -m src.cli analyze log.txt --llm --mode ml-only
  • View analytics: python scripts/analytics.py stats
  • Continue collecting feedback to improve further
            """.strip(),
            title="📊 Retraining Summary",
            border_style="green"
        ))
        console.print()
        
    except Exception as e:
        console.print(f"\n[red]❌ Error during retraining: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


if __name__ == '__main__':
    app()
