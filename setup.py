#!/usr/bin/env python3
"""
AI-LogGuard Setup Configuration
Allows installation as a CLI tool: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="ai-logguard",
    version="1.0.0",
    author="SyLe-Van",
    author_email="your.email@example.com",
    description="🤖 AI-powered CLI for CI/CD log analysis with ML + LLM hybrid intelligence",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SyLe-Van/AI-LogGuard",
    project_urls={
        "Bug Tracker": "https://github.com/SyLe-Van/AI-LogGuard/issues",
        "Documentation": "https://github.com/SyLe-Van/AI-LogGuard#readme",
        "Source Code": "https://github.com/SyLe-Van/AI-LogGuard",
    },
    packages=find_packages(exclude=["tests", "tests.*", "notebooks", "notebooks.*", "scripts"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.1.1",
            "pytest-cov>=5.0.0",
            "black>=24.3.0",
            "flake8>=7.0.0",
            "mypy>=1.9.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "numpy>=1.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ailog=src.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": [
            "models/*.pkl",
            "data/*.db",
        ],
    },
    keywords=[
        "ci-cd",
        "log-analysis",
        "machine-learning",
        "llm",
        "devops",
        "automation",
        "jenkins",
        "github-actions",
        "gitlab",
        "error-detection",
        "ai",
    ],
    zip_safe=False,
)
