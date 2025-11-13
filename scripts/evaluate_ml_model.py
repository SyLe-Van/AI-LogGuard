#!/usr/bin/env python3
"""
Evaluate ML Model Performance
Generate detailed metrics and classification report
"""

import joblib
import numpy as np
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score,
    classification_report,
    confusion_matrix
)
from rich.console import Console
from rich.table import Table

console = Console()

def evaluate_model():
    """Evaluate Random Forest model performance"""
    
    model_dir = Path(__file__).parent.parent / 'models'
    
    # Load model and data
    console.print("\n[bold cyan]📊 Loading Model and Test Data...[/bold cyan]\n")
    
    model = joblib.load(model_dir / 'error_classifier_rf.pkl')
    label_encoder = joblib.load(model_dir / 'label_encoder.pkl')
    metadata = joblib.load(model_dir / 'model_metadata.pkl')
    
    X_test = joblib.load(model_dir / 'X_test.pkl')
    y_test = joblib.load(model_dir / 'y_test.pkl')
    
    X_val = joblib.load(model_dir / 'X_val.pkl')
    y_val = joblib.load(model_dir / 'y_val.pkl')
    
    # Predictions
    y_test_pred = model.predict(X_test)
    y_val_pred = model.predict(X_val)
    
    # Get class names
    classes = label_encoder.classes_
    
    # ========================================
    # 1. MODEL INFO
    # ========================================
    console.print("[bold magenta]🤖 MODEL INFORMATION[/bold magenta]")
    console.print("="*70)
    
    info_table = Table(show_header=True, header_style="bold cyan")
    info_table.add_column("Metric", style="yellow")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Model Type", metadata['best_model'])
    info_table.add_row("Total Features", str(metadata['num_features']))
    info_table.add_row("TF-IDF Features", str(metadata.get('tfidf_features', 'N/A')))
    info_table.add_row("Structural Features", str(metadata.get('structural_features', 'N/A')))
    info_table.add_row("Training Samples", str(metadata['training_samples']))
    info_table.add_row("Number of Classes", str(len(classes)))
    info_table.add_row("Inference Time", f"{metadata['inference_time_ms']:.2f} ms")
    
    console.print(info_table)
    console.print()
    
    # ========================================
    # 2. OVERALL METRICS
    # ========================================
    console.print("[bold magenta]📈 OVERALL PERFORMANCE METRICS[/bold magenta]")
    console.print("="*70)
    
    metrics_table = Table(show_header=True, header_style="bold cyan")
    metrics_table.add_column("Dataset", style="yellow")
    metrics_table.add_column("Accuracy", justify="right")
    metrics_table.add_column("Precision", justify="right")
    metrics_table.add_column("Recall", justify="right")
    metrics_table.add_column("F1-Score", justify="right")
    
    # Test set metrics
    test_acc = accuracy_score(y_test, y_test_pred)
    test_prec = precision_score(y_test, y_test_pred, average='weighted', zero_division=0)
    test_rec = recall_score(y_test, y_test_pred, average='weighted', zero_division=0)
    test_f1 = f1_score(y_test, y_test_pred, average='weighted', zero_division=0)
    
    metrics_table.add_row(
        "Test Set",
        f"[green]{test_acc:.2%}[/green]",
        f"[green]{test_prec:.2%}[/green]",
        f"[green]{test_rec:.2%}[/green]",
        f"[green]{test_f1:.2%}[/green]"
    )
    
    # Validation set metrics
    val_acc = accuracy_score(y_val, y_val_pred)
    val_prec = precision_score(y_val, y_val_pred, average='weighted', zero_division=0)
    val_rec = recall_score(y_val, y_val_pred, average='weighted', zero_division=0)
    val_f1 = f1_score(y_val, y_val_pred, average='weighted', zero_division=0)
    
    metrics_table.add_row(
        "Validation Set",
        f"[green]{val_acc:.2%}[/green]",
        f"[green]{val_prec:.2%}[/green]",
        f"[green]{val_rec:.2%}[/green]",
        f"[green]{val_f1:.2%}[/green]"
    )
    
    console.print(metrics_table)
    console.print()
    
    # ========================================
    # 3. PER-CLASS METRICS
    # ========================================
    console.print("[bold magenta]🎯 PER-CLASS PERFORMANCE (Test Set)[/bold magenta]")
    console.print("="*70)
    
    # Classification report
    report = classification_report(y_test, y_test_pred, target_names=classes, output_dict=True, zero_division=0)
    
    class_table = Table(show_header=True, header_style="bold cyan")
    class_table.add_column("Error Class", style="yellow")
    class_table.add_column("Precision", justify="right")
    class_table.add_column("Recall", justify="right")
    class_table.add_column("F1-Score", justify="right")
    class_table.add_column("Support", justify="right")
    
    for cls in classes:
        if cls in report:
            class_table.add_row(
                cls,
                f"{report[cls]['precision']:.2%}",
                f"{report[cls]['recall']:.2%}",
                f"{report[cls]['f1-score']:.2%}",
                str(int(report[cls]['support']))
            )
    
    console.print(class_table)
    console.print()
    
    # ========================================
    # 4. CONFUSION MATRIX
    # ========================================
    console.print("[bold magenta]🔀 CONFUSION MATRIX (Test Set)[/bold magenta]")
    console.print("="*70)
    
    cm = confusion_matrix(y_test, y_test_pred)
    
    cm_table = Table(show_header=True, header_style="bold cyan")
    cm_table.add_column("True \\ Pred", style="yellow")
    
    for cls in classes:
        cm_table.add_column(cls[:12], justify="right")
    
    for i, true_cls in enumerate(classes):
        row = [true_cls[:12]]
        for j, pred_cls in enumerate(classes):
            val = cm[i][j]
            if i == j:
                # Diagonal (correct predictions)
                row.append(f"[green]{val}[/green]")
            elif val > 0:
                # Off-diagonal (mistakes)
                row.append(f"[red]{val}[/red]")
            else:
                row.append(f"[dim]{val}[/dim]")
        cm_table.add_row(*row)
    
    console.print(cm_table)
    console.print()
    
    # ========================================
    # 5. SUMMARY
    # ========================================
    console.print("[bold magenta]📋 SUMMARY[/bold magenta]")
    console.print("="*70)
    
    summary_points = [
        f"✅ Test Accuracy: [bold green]{test_acc:.2%}[/bold green]",
        f"✅ Test F1-Score: [bold green]{test_f1:.2%}[/bold green]",
        f"✅ Validation Accuracy: [bold green]{val_acc:.2%}[/bold green]",
        f"✅ Total Classes: [bold]{len(classes)}[/bold]",
        f"✅ Test Samples: [bold]{len(y_test)}[/bold]",
        f"✅ Inference Speed: [bold]{metadata['inference_time_ms']:.2f} ms[/bold]",
    ]
    
    for point in summary_points:
        console.print(f"  {point}")
    
    console.print("\n" + "="*70)
    
    # ========================================
    # 6. STRENGTHS & WEAKNESSES
    # ========================================
    console.print("\n[bold magenta]💪 MODEL STRENGTHS & WEAKNESSES[/bold magenta]")
    console.print("="*70)
    
    console.print("\n[bold green]Strengths:[/bold green]")
    if test_acc >= 0.95:
        console.print("  ✅ Excellent accuracy (>95%)")
    elif test_acc >= 0.85:
        console.print("  ✅ Good accuracy (85-95%)")
    
    if metadata['inference_time_ms'] < 50:
        console.print("  ✅ Fast inference (<50ms)")
    
    console.print("  ✅ Multi-class classification (7 error types)")
    console.print("  ✅ Hybrid features (TF-IDF + Structural)")
    
    console.print("\n[bold yellow]Potential Improvements:[/bold yellow]")
    
    # Check for low-performing classes
    weak_classes = [cls for cls in classes if report[cls]['f1-score'] < 0.80]
    if weak_classes:
        console.print(f"  ⚠️  Some classes have F1 < 80%: {', '.join(weak_classes)}")
    
    if len(y_test) < 50:
        console.print(f"  ⚠️  Small test set ({len(y_test)} samples) - consider more data")
    
    if metadata['training_samples'] < 500:
        console.print(f"  ⚠️  Training set could be larger ({metadata['training_samples']} samples)")
    
    console.print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    evaluate_model()
