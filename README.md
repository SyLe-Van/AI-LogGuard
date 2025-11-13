# 🤖 AI-LogGuard

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **AI-powered Cross-platform CLI for CI/CD Log Analysis, Failure Prediction, and Auto-fix Suggestion (Hybrid ML + LLM)**

AI-LogGuard is an intelligent command-line tool that automatically analyzes CI/CD build logs, predicts failure types using machine learning, and provides actionable fix suggestions powered by Large Language Models.

## 🌟 Features

### ✅ Phase 1 (Current - Completed)

- 🔍 **Smart Log Parsing**: Automatically detects and parses logs from:
  - Jenkins
  - GitHub Actions
  - GitLab CI (coming soon)
- 📊 **Beautiful CLI Output**: Rich terminal interface with colors, tables, and progress indicators
- 🎯 **Unified Schema**: Consistent data structure across all CI/CD platforms
- 📈 **Detailed Analysis**: Extracts errors, warnings, stages, retries, and statistics

### 🚧 Coming Soon

- 🤖 **ML Classification**: Predict error categories (dependency, syntax, timeout, etc.)
- 🧠 **LLM Analysis**: Generate summaries and detailed explanations
- 💡 **Auto-fix Suggestions**: Get actionable steps to resolve failures
- 📚 **Feedback Loop**: Continuously improve with user feedback
- 🔄 **Self-learning**: Model retraining with new data

## 🚀 Quick Start

### Where to Install & Run

AI-LogGuard is a **standalone CLI tool** that runs on your local machine or a dedicated analysis server. It does NOT need to be installed on your Jenkins/CI server.

**Typical Setup:**

```
┌─────────────────┐
│ Jenkins Server  │  ← Your CI/CD runs here (Docker/EC2)
│ - Builds logs   │
└────────┬────────┘
         │ Fetch via API or export logs
         ▼
┌─────────────────┐
│ Your Machine    │  ← Install AI-LogGuard here
│ - AI-LogGuard   │
│ - Analyze logs  │
└─────────────────┘
```

**Three ways to use:**

1. **Local Analysis** (Simplest): Download log → Run `ai-logguard analyze log.txt`
2. **Remote Fetch**: Use `ai-logguard fetch` to pull logs via Jenkins API
3. **Analysis Server**: Install on dedicated EC2/server for automated analysis

### Installation

```bash
# Clone the repository
git clone https://github.com/SyLe-Van/AI-LogGuard.git
cd AI-LogGuard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

**For production server:**

```bash
# On your analysis server (EC2/VPS)
sudo apt update && sudo apt install python3-pip python3-venv
git clone https://github.com/SyLe-Van/AI-LogGuard.git
cd AI-LogGuard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Usage

#### Analyze a log file

```bash
ai-logguard analyze tests/sample_logs.txt
```

#### Get a quick summary

```bash
ai-logguard summarize tests/sample_logs.txt
```

#### Fetch logs from Jenkins

```bash
ai-logguard fetch \
  --provider jenkins \
  --url http://localhost:8080 \
  --job-id my-job \
  --token YOUR_TOKEN \
  --build lastBuild \
  --save fetched.log
```

#### Output formats

```bash
# Rich terminal output (default)
ai-logguard analyze log.txt

# JSON output
ai-logguard analyze log.txt --format json

# Markdown output
ai-logguard analyze log.txt --format markdown

# Show full details
ai-logguard analyze log.txt --full
```

## 📖 Documentation

See [ROADMAP.md](ROADMAP.md) for detailed development plan and progress.

### Project Structure

```
ai-logguard/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI commands (Typer)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Unified data models (Pydantic)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py   # Base parser interface
│   │   ├── jenkins_parser.py
│   │   ├── github_actions_parser.py
│   │   └── factory.py       # Auto-detection
│   ├── fetchers/
│   │   ├── jenkins_fetcher.py
│   │   └── gitlab_fetcher.py
│   └── utils/
│       ├── __init__.py
│       └── display.py       # Rich output formatting
├── tests/
│   ├── sample_logs.txt
│   ├── test_parser.py
│   └── test_jenkins_fetcher.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 🛠 Development

### Run tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=src --cov-report=html
```

### Code formatting

```bash
black src/ tests/
isort src/ tests/
```

### Type checking

```bash
mypy src/
```

## 📊 Example Output

```
🔍 Analyzing log file: tests/sample_logs.txt

✅ Log file loaded
✅ Log parsed successfully

╭─ 🔧 JENKINS - test-job ───────────────────────────────────────────╮
│ Build: N/A                                                         │
│ Status: ⚠️ UNSTABLE                                               │
│ Triggered by: Sy Le                                                │
╰────────────────────────────────────────────────────────────────────╯

                           📊 Statistics
┏━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric        ┃ Count ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Lines   │   121 │
│ Stages/Steps  │     1 │
│ Errors        │     5 │
│ Warnings      │     7 │
│ Retries       │     4 │
└───────────────┴───────┘

🎯 Stages/Steps
└── ✅ Simulate Build Logs - SUCCESS (5 errors, 7 warnings, 4 retries)

❌ Errors (showing 5 of 5)
┏━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Line ┃ Level   ┃ Message                                         ┃
┡━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 23   │ ERROR   │ [ERROR] Failed to fetch dependency: lib-xyz     │
│ 39   │ ERROR   │ [ERROR] Compilation failed in module: invoice   │
│ 53   │ ERROR   │ [ERROR] Unit test failed: test_order_checkout   │
│ 63   │ ERROR   │ [ERROR] DB connection timeout on first try      │
│ 85   │ ERROR   │ [ERROR] Deployment failed due to timeout        │
└──────┴─────────┴─────────────────────────────────────────────────┘
```

## 🎯 Roadmap

- [x] **Phase 1**: Foundation & Basic Parsing (Week 1-2) ✅
  - [x] CLI structure with Typer
  - [x] Jenkins & GitHub Actions parsers
  - [x] Unified log schema
  - [x] Rich terminal output
- [ ] **Phase 2**: LLM Integration (Week 3-4)
  - [ ] OpenAI API integration
  - [ ] Prompt engineering
  - [ ] Summarization & explanation
  - [ ] Fix suggestions
- [ ] **Phase 3**: ML Model Training (Week 5-6)
  - [ ] Dataset collection
  - [ ] Feature engineering
  - [ ] Model training (Random Forest, Logistic Regression)
  - [ ] Hybrid ML + LLM pipeline
- [ ] **Phase 4**: Feedback Loop (Week 7-8)
  - [ ] User feedback collection
  - [ ] Analytics dashboard
  - [ ] Automated retraining
- [ ] **Phase 5**: Production Ready (Week 9-10)
  - [ ] Performance optimization
  - [ ] Packaging (PyPI, Docker)
  - [ ] Complete documentation

## 🤝 Contributing

Contributions are welcome! This is a thesis project, but suggestions and feedback are appreciated.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 👤 Author

**Sy Le Van**

- GitHub: [@SyLe-Van](https://github.com/SyLe-Van)
- Thesis: AI-powered Cross-platform CLI for CI/CD Log Analysis

---

**Note**: This is an active thesis project. Features are being developed according to the roadmap.

```

```
