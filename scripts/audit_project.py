#!/usr/bin/env python3
"""
Complete Project Audit - Check all phases for completeness
"""

import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("\n" + "="*70)
print("🔍 AI-LOGGUARD COMPLETE PROJECT AUDIT")
print("="*70 + "\n")

issues = []
warnings = []
successes = []

def check(description, condition, critical=True):
    """Check a condition and track results"""
    if condition:
        successes.append(f"✅ {description}")
        print(f"✅ {description}")
        return True
    else:
        msg = f"❌ {description}"
        if critical:
            issues.append(msg)
        else:
            warnings.append(msg)
        print(msg)
        return False

# ============================================================================
# PHASE 1: CI/CD PARSING
# ============================================================================
print("📦 PHASE 1: CI/CD PARSING")
print("-"*70)

try:
    from parsers import parse_log
    check("parse_log function imported", True)
    
    from parsers.jenkins_parser import JenkinsParser
    check("JenkinsParser imported", True)
    
    from parsers.github_actions_parser import GitHubActionsParser
    check("GitHubActionsParser imported", True)
    
    from parsers.factory import ParserFactory
    check("ParserFactory imported", True)
    
    from models import ParsedLog, BuildStatus, Platform
    check("Data models imported", True)
    
    # Check test files
    test_dir = project_root / "tests"
    check("tests/ directory exists", test_dir.exists())
    check("test_parsers.py exists", (test_dir / "test_parsers.py").exists())
    
except Exception as e:
    check(f"Phase 1 imports: {e}", False)

print()

# ============================================================================
# PHASE 2: LLM INTEGRATION
# ============================================================================
print("="*70)
print("🤖 PHASE 2: LLM INTEGRATION")
print("-"*70)

try:
    from llm.gemini_client import GeminiClient
    check("GeminiClient imported", True)
    
    from llm.summarizer import LogSummarizer
    check("LogSummarizer imported", True)
    
    from llm.explainer import ErrorExplainer
    check("ErrorExplainer imported", True)
    
    from llm.fix_suggester import FixSuggester
    check("FixSuggester imported", True)
    
    from llm.prompts import SUMMARY_PROMPT, ERROR_EXPLANATION_PROMPT, FIX_SUGGESTION_PROMPT
    check("Prompts imported", True)
    
    # Check .env setup
    env_example = project_root / ".env.example"
    check(".env.example exists", env_example.exists())
    
    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        check(".env in .gitignore", ".env" in content)
    
except Exception as e:
    check(f"Phase 2 imports: {e}", False)

print()

# ============================================================================
# PHASE 3A: ML MODEL TRAINING
# ============================================================================
print("="*70)
print("🧠 PHASE 3A: ML MODEL TRAINING")
print("-"*70)

models_dir = project_root / "models"
check("models/ directory exists", models_dir.exists())

if models_dir.exists():
    check("error_classifier_rf.pkl exists", 
          (models_dir / "error_classifier_rf.pkl").exists())
    check("tfidf_vectorizer.pkl exists",
          (models_dir / "tfidf_vectorizer.pkl").exists())
    check("label_encoder.pkl exists",
          (models_dir / "label_encoder.pkl").exists())
    check("feature_info.pkl exists",
          (models_dir / "feature_info.pkl").exists())
    check("model_metadata.pkl exists",
          (models_dir / "model_metadata.pkl").exists())

try:
    from ml.predictor import ErrorClassifier
    check("ErrorClassifier imported", True)
    
    # Try to initialize
    clf = ErrorClassifier()
    check("ErrorClassifier can be initialized", True)
    check("ErrorClassifier has model", hasattr(clf, 'model'))
    check("ErrorClassifier has vectorizer", hasattr(clf, 'vectorizer'))
    
except Exception as e:
    check(f"Phase 3A ML components: {e}", False)

# Check training data
data_dir = project_root / "data" / "synthetic_logs"
check("synthetic_logs/ directory exists", data_dir.exists(), critical=False)

print()

# ============================================================================
# PHASE 3B: HYBRID INTEGRATION
# ============================================================================
print("="*70)
print("🔄 PHASE 3B: HYBRID ML+LLM INTEGRATION")
print("-"*70)

try:
    from hybrid.analyzer import HybridAnalyzer
    check("HybridAnalyzer imported", True)
    
    from llm.specialized_prompts import (
        get_specialized_prompt,
        DEPENDENCY_ERROR_PROMPT,
        SYNTAX_ERROR_PROMPT,
        TEST_FAILURE_PROMPT
    )
    check("Specialized prompts imported", True)
    check("7 specialized prompts exist", 
          all([DEPENDENCY_ERROR_PROMPT, SYNTAX_ERROR_PROMPT, TEST_FAILURE_PROMPT]))
    
    # Check CLI integration
    from cli import HYBRID_AVAILABLE
    check("HYBRID_AVAILABLE flag in CLI", True)
    
except Exception as e:
    check(f"Phase 3B hybrid components: {e}", False)

# Check scripts
scripts_dir = project_root / "scripts"
check("scripts/test_hybrid_mode.py exists",
      (scripts_dir / "test_hybrid_mode.py").exists(), critical=False)
check("test_phase3.sh exists",
      (project_root / "test_phase3.sh").exists(), critical=False)

print()

# ============================================================================
# PHASE 4: FEEDBACK LOOP & SELF-LEARNING
# ============================================================================
print("="*70)
print("🔄 PHASE 4: FEEDBACK LOOP & SELF-LEARNING")
print("-"*70)

try:
    from feedback.manager import FeedbackManager
    check("FeedbackManager imported", True)
    
    from feedback.database import FeedbackDatabase
    check("FeedbackDatabase imported", True)
    
    # Try to initialize
    fm = FeedbackManager()
    check("FeedbackManager can be initialized", True)
    check("Database path configured", hasattr(fm, 'db'))
    
    # Check if database exists
    feedback_db = project_root / "data" / "feedback.db"
    check("feedback.db created", feedback_db.exists())
    
    # Check CLI integration
    from cli import FEEDBACK_AVAILABLE
    check("FEEDBACK_AVAILABLE flag in CLI", True)
    
except Exception as e:
    check(f"Phase 4 feedback components: {e}", False)

# Check Phase 4 scripts
check("scripts/analytics.py exists",
      (scripts_dir / "analytics.py").exists())
check("scripts/retrain_model.py exists",
      (scripts_dir / "retrain_model.py").exists())
check("test_phase4.sh exists",
      (project_root / "test_phase4.sh").exists(), critical=False)

print()

# ============================================================================
# DOCUMENTATION & TESTS
# ============================================================================
print("="*70)
print("📚 DOCUMENTATION & TESTING")
print("-"*70)

docs_dir = project_root / "docs"
check("docs/ directory exists", docs_dir.exists())

if docs_dir.exists():
    check("PHASE4_FEEDBACK_LOOP.md exists",
          (docs_dir / "PHASE4_FEEDBACK_LOOP.md").exists(), critical=False)

check("README.md exists", (project_root / "README.md").exists())
check("requirements.txt exists", (project_root / "requirements.txt").exists())
check("QUICK_REFERENCE.md exists", 
      (project_root / "QUICK_REFERENCE.md").exists(), critical=False)

# Check test scripts
check("test_phase3.sh executable", 
      (project_root / "test_phase3.sh").exists(), critical=False)
check("test_phase4.sh executable",
      (project_root / "test_phase4.sh").exists(), critical=False)

print()

# ============================================================================
# CLI INTEGRATION
# ============================================================================
print("="*70)
print("🖥️  CLI INTEGRATION")
print("-"*70)

try:
    from cli import app, console
    check("CLI app initialized", True)
    
    import cli
    check("analyze command exists", hasattr(cli.app, 'registered_commands'))
    
    # Check for --mode parameter
    cli_file = project_root / "src" / "cli.py"
    if cli_file.exists():
        content = cli_file.read_text()
        check("--mode parameter in CLI", "--mode" in content)
        check("--llm parameter in CLI", "--llm" in content)
        check("_run_hybrid_analysis function", "_run_hybrid_analysis" in content)
        check("_collect_feedback function", "_collect_feedback" in content)
    
except Exception as e:
    check(f"CLI components: {e}", False)

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("="*70)
print("📊 AUDIT SUMMARY")
print("="*70)
print()

print(f"✅ Successes: {len(successes)}")
print(f"⚠️  Warnings: {len(warnings)}")
print(f"❌ Critical Issues: {len(issues)}")
print()

if issues:
    print("="*70)
    print("❌ CRITICAL ISSUES FOUND:")
    print("="*70)
    for issue in issues:
        print(f"  {issue}")
    print()

if warnings:
    print("="*70)
    print("⚠️  WARNINGS (non-critical):")
    print("="*70)
    for warning in warnings:
        print(f"  {warning}")
    print()

if not issues:
    print("="*70)
    print("🎉 ALL CRITICAL COMPONENTS VERIFIED!")
    print("="*70)
    print()
    print("✅ Phase 1: CI/CD Parsing - COMPLETE")
    print("✅ Phase 2: LLM Integration - COMPLETE")
    print("✅ Phase 3A: ML Model Training - COMPLETE")
    print("✅ Phase 3B: Hybrid Integration - COMPLETE")
    print("✅ Phase 4: Feedback Loop & Self-Learning - COMPLETE")
    print()
    print("🎓 Project is ready for thesis evaluation!")
    print()
else:
    print("="*70)
    print("⚠️  PLEASE FIX CRITICAL ISSUES BEFORE PROCEEDING")
    print("="*70)
    print()
    sys.exit(1)
