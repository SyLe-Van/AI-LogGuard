"""
Synthetic CI/CD Log Dataset Generator for ML Training

Generates realistic, labeled CI/CD logs with various error types.
Perfect for training error classification models when real data is limited.

Usage:
    python scripts/generate_synthetic_dataset.py --output data/synthetic_logs --count 300
"""

import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import argparse


class SyntheticLogGenerator:
    """Generate realistic synthetic CI/CD logs with error types"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.platforms = ["jenkins", "github-actions", "gitlab-ci"]
        
        # Error categories and their weights
        self.error_categories = {
            "dependency_error": 0.25,
            "syntax_error": 0.20,
            "test_failure": 0.20,
            "timeout": 0.15,
            "environment_error": 0.10,
            "network_error": 0.05,
            "permission_error": 0.05,
        }
        
        # Templates for each error type
        self.templates = self._create_templates()
        
    def _create_templates(self) -> Dict:
        """Create error templates for each category"""
        return {
            "dependency_error": {
                "npm": [
                    {
                        "error_pattern": "npm ERR! code E404\nnpm ERR! 404 Not Found - GET https://registry.npmjs.org/{package}\nnpm ERR! 404  '{package}@{version}' is not in the npm registry.",
                        "packages": ["react-dom", "@types/node", "webpack", "eslint", "typescript"],
                        "versions": ["^18.0.0", "1.2.3", "^5.0.0", "latest", "^4.5.0"],
                    },
                    {
                        "error_pattern": "npm ERR! code ERESOLVE\nnpm ERR! ERESOLVE could not resolve\nnpm ERR! peer {package}@\"{version}\" from {dependent}",
                        "packages": ["react", "react-dom", "typescript", "webpack"],
                        "versions": [">=17.0.0", "^16.0.0", "^4.0.0", "^5.0.0"],
                        "dependents": ["react-scripts@5.0.0", "next@12.0.0", "gatsby@4.0.0"],
                    },
                ],
                "pip": [
                    {
                        "error_pattern": "ERROR: Could not find a version that satisfies the requirement {package}=={version}\nERROR: No matching distribution found for {package}=={version}",
                        "packages": ["tensorflow", "pandas", "numpy", "scikit-learn", "matplotlib"],
                        "versions": ["2.10.0", "1.5.0", "1.23.0", "1.2.0", "3.6.0"],
                    },
                    {
                        "error_pattern": "ERROR: {package} has requirement {dependency}!={version}, but you have {dependency} {installed_version}",
                        "packages": ["flask", "django", "requests", "boto3"],
                        "dependencies": ["Werkzeug", "sqlalchemy", "urllib3", "botocore"],
                        "versions": ["2.0.0", "1.4.0", "1.26.0"],
                        "installed_versions": ["2.2.0", "1.3.0", "2.0.0"],
                    },
                ],
                "maven": [
                    {
                        "error_pattern": "[ERROR] Failed to execute goal on project {project}: Could not resolve dependencies for project {group}:{artifact}:{version}\n[ERROR] The following artifacts could not be resolved: {dependency}",
                        "projects": ["my-app", "user-service", "api-gateway"],
                        "groups": ["com.example", "org.springframework", "io.github"],
                        "artifacts": ["core", "web", "data-jpa"],
                        "versions": ["1.0.0-SNAPSHOT", "2.5.0", "3.0.0"],
                        "dependencies": ["org.slf4j:slf4j-api:jar:1.7.32", "junit:junit:jar:4.13"],
                    },
                ],
            },
            
            "syntax_error": {
                "typescript": [
                    {
                        "error_pattern": "src/{file}.ts({line},{col}): error TS{code}: {message}",
                        "files": ["index", "utils/helper", "components/Button", "api/client"],
                        "lines": range(10, 500),
                        "cols": range(1, 80),
                        "codes": [
                            ("2322", "Type 'string' is not assignable to type 'number'"),
                            ("2304", "Cannot find name 'process'"),
                            ("2345", "Argument of type 'null' is not assignable to parameter"),
                            ("2339", "Property 'map' does not exist on type 'undefined'"),
                            ("2551", "Property 'lenght' does not exist on type 'string[]'. Did you mean 'length'?"),
                        ],
                    },
                ],
                "python": [
                    {
                        "error_pattern": "  File \"{file}.py\", line {line}\n    {code_line}\n    {pointer}\n{error_type}: {message}",
                        "files": ["main", "utils/helpers", "models/user", "api/routes"],
                        "lines": range(10, 300),
                        "errors": [
                            ("SyntaxError", "invalid syntax", "return x +", "         ^"),
                            ("IndentationError", "unexpected indent", "    print(x)", "    ^"),
                            ("SyntaxError", "unexpected EOF while parsing", "def func():", "          ^"),
                            ("SyntaxError", "invalid character in identifier", "café = 10", "    ^"),
                        ],
                    },
                ],
                "java": [
                    {
                        "error_pattern": "{file}.java:[{line},{col}] error: {message}",
                        "files": ["Main", "UserService", "ApiController"],
                        "lines": range(10, 400),
                        "cols": range(1, 80),
                        "messages": [
                            "';' expected",
                            "cannot find symbol: variable x",
                            "incompatible types: String cannot be converted to int",
                            "method doSomething() is already defined in class Main",
                        ],
                    },
                ],
            },
            
            "test_failure": {
                "jest": [
                    {
                        "error_pattern": "FAIL {file}\n  ● {test_suite} › {test_name}\n\n    expect(received).{matcher}\n\n    Expected: {expected}\n    Received: {received}",
                        "files": ["src/__tests__/auth.test.ts", "tests/user.test.js"],
                        "test_suites": ["UserAuth", "API Integration", "Component Rendering"],
                        "test_names": ["should login with valid credentials", "should return 404 for unknown user", "should render without crashing"],
                        "matchers": ["toBe(200)", "toEqual({...})", "toHaveBeenCalled()"],
                        "expecteds": ["200", "{ status: 'success' }", "true"],
                        "receiveds": ["401", "{ status: 'error' }", "false"],
                    },
                ],
                "pytest": [
                    {
                        "error_pattern": "FAILED {file}::{test_class}::{test_name}\nE       AssertionError: {message}\nE       assert {actual} == {expected}",
                        "files": ["tests/test_models.py", "tests/test_api.py"],
                        "test_classes": ["TestUser", "TestAPI", "TestDatabase"],
                        "test_names": ["test_create_user", "test_login", "test_get_user"],
                        "messages": ["User creation failed", "Invalid response", "Expected 200"],
                        "actuals": ["None", "401", "[]"],
                        "expecteds": ["User(id=1)", "200", "[User(...)]"],
                    },
                ],
            },
            
            "timeout": [
                {
                    "error_pattern": "Error: Timeout of {timeout}ms exceeded. For async tests and hooks, ensure \"done()\" is called",
                    "timeouts": [2000, 5000, 10000, 30000],
                },
                {
                    "error_pattern": "FATAL: command execution failed\nBuild timed out (after {minutes} minutes). Marking the build as aborted.",
                    "minutes": [10, 15, 30, 60],
                },
            ],
            
            "environment_error": [
                {
                    "error_pattern": "Error: ENOENT: no such file or directory, open '{file}'",
                    "files": [".env", "config.json", "credentials.yaml", "package.json"],
                },
                {
                    "error_pattern": "Error: {variable} is not defined\nReferenceError: {variable} is not defined",
                    "variables": ["process.env.API_KEY", "DATABASE_URL", "SECRET_KEY", "PORT"],
                },
            ],
            
            "network_error": [
                {
                    "error_pattern": "Error: connect ETIMEDOUT {host}:{port}\nError: getaddrinfo ENOTFOUND {host}",
                    "hosts": ["api.example.com", "registry.npmjs.org", "github.com"],
                    "ports": [443, 80, 5432, 27017],
                },
            ],
            
            "permission_error": [
                {
                    "error_pattern": "Error: EACCES: permission denied, {operation} '{path}'",
                    "operations": ["mkdir", "open", "unlink", "chmod"],
                    "paths": ["/usr/local/bin", "/var/log", "~/.npm", "/opt/app"],
                },
            ],
        }
    
    def generate_log_header(self, platform: str, build_number: int) -> str:
        """Generate realistic log header"""
        timestamp = datetime.now() - timedelta(days=random.randint(0, 30))
        
        if platform == "jenkins":
            return f"""Started by user admin
Running as SYSTEM
Building in workspace /var/jenkins_home/workspace/my-project
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/my-project
[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Checkout SCM
"""
        elif platform == "github-actions":
            return f"""Run {build_number}
Triggered by push event
GITHUB_WORKFLOW: CI
GITHUB_RUN_ID: {build_number}
GITHUB_RUN_NUMBER: {build_number}
{timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')} ##[group]Setting up job
"""
        else:  # gitlab-ci
            return f"""Running with gitlab-runner 14.10.0 (abc123)
  on runner-xyz {build_number}
Preparing the "docker" executor
{timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def generate_build_context(self, platform: str) -> str:
        """Generate build context (steps before error)"""
        steps = [
            "Installing dependencies...",
            "Running npm install",
            "Found 0 vulnerabilities",
            "Compiling TypeScript...",
            "Building production bundle...",
            "Running tests...",
        ]
        return "\n".join([f"[{platform}] {step}" for step in random.sample(steps, k=random.randint(3, 5))])
    
    def generate_error_log(self, error_category: str, platform: str) -> Dict:
        """Generate a single error log"""
        
        # Select template based on category
        if error_category == "dependency_error":
            pkg_manager = random.choice(["npm", "pip", "maven"])
            template = random.choice(self.templates["dependency_error"][pkg_manager])
            
            error_text = template["error_pattern"]
            if pkg_manager == "npm":
                error_text = error_text.format(
                    package=random.choice(template["packages"]),
                    version=random.choice(template["versions"]),
                    dependent=random.choice(template.get("dependents", [""])) if "dependents" in template else ""
                )
            elif pkg_manager == "pip":
                error_text = error_text.format(
                    package=random.choice(template["packages"]),
                    version=random.choice(template.get("versions", [""])),
                    dependency=random.choice(template.get("dependencies", [""])),
                    installed_version=random.choice(template.get("installed_versions", [""]))
                )
            else:  # maven
                error_text = error_text.format(
                    project=random.choice(template["projects"]),
                    group=random.choice(template["groups"]),
                    artifact=random.choice(template["artifacts"]),
                    version=random.choice(template["versions"]),
                    dependency=random.choice(template["dependencies"])
                )
                
        elif error_category == "syntax_error":
            lang = random.choice(["typescript", "python", "java"])
            template = random.choice(self.templates["syntax_error"][lang])
            
            if lang == "typescript":
                code_info = random.choice(template["codes"])
                error_text = template["error_pattern"].format(
                    file=random.choice(template["files"]),
                    line=random.choice(template["lines"]),
                    col=random.choice(template["cols"]),
                    code=code_info[0],
                    message=code_info[1]
                )
            elif lang == "python":
                error_info = random.choice(template["errors"])
                error_text = template["error_pattern"].format(
                    file=random.choice(template["files"]),
                    line=random.choice(template["lines"]),
                    code_line=error_info[2],
                    pointer=error_info[3],
                    error_type=error_info[0],
                    message=error_info[1]
                )
            else:  # java
                error_text = template["error_pattern"].format(
                    file=random.choice(template["files"]),
                    line=random.choice(template["lines"]),
                    col=random.choice(template["cols"]),
                    message=random.choice(template["messages"])
                )
                
        elif error_category == "test_failure":
            framework = random.choice(["jest", "pytest"])
            template = random.choice(self.templates["test_failure"][framework])
            
            if framework == "jest":
                error_text = template["error_pattern"].format(
                    file=random.choice(template["files"]),
                    test_suite=random.choice(template["test_suites"]),
                    test_name=random.choice(template["test_names"]),
                    matcher=random.choice(template["matchers"]),
                    expected=random.choice(template["expecteds"]),
                    received=random.choice(template["receiveds"])
                )
            else:  # pytest
                error_text = template["error_pattern"].format(
                    file=random.choice(template["files"]),
                    test_class=random.choice(template["test_classes"]),
                    test_name=random.choice(template["test_names"]),
                    message=random.choice(template["messages"]),
                    actual=random.choice(template["actuals"]),
                    expected=random.choice(template["expecteds"])
                )
        else:
            # Simple error categories
            template = random.choice(self.templates[error_category])
            error_text = template["error_pattern"]
            
            # Fill in placeholders
            for key, values in template.items():
                if key != "error_pattern" and isinstance(values, list):
                    error_text = error_text.replace(f"{{{key}}}", str(random.choice(values)))
        
        # Build complete log
        build_number = random.randint(1, 1000)
        header = self.generate_log_header(platform, build_number)
        context = self.generate_build_context(platform)
        footer = f"\n[{platform}] Build failed with exit code 1\nFailed build #{build_number}"
        
        full_log = f"{header}\n{context}\n\nERROR:\n{error_text}\n{footer}"
        
        return {
            "log_id": f"{platform}_{error_category}_{build_number}",
            "platform": platform,
            "error_category": error_category,
            "error_text": error_text,
            "full_log": full_log,
            "build_number": build_number,
            "timestamp": datetime.now().isoformat(),
        }
    
    def generate_dataset(self, total_count: int = 300) -> List[Dict]:
        """Generate complete dataset"""
        dataset = []
        
        # Calculate counts per category
        for category, weight in self.error_categories.items():
            count = int(total_count * weight)
            
            for _ in range(count):
                platform = random.choice(self.platforms)
                log_entry = self.generate_error_log(category, platform)
                dataset.append(log_entry)
        
        # Shuffle
        random.shuffle(dataset)
        
        return dataset
    
    def save_dataset(self, dataset: List[Dict], output_dir: Path):
        """Save dataset to files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual log files
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = []
        
        for i, entry in enumerate(dataset):
            # Save log file
            log_file = logs_dir / f"{entry['log_id']}.txt"
            log_file.write_text(entry['full_log'])
            
            # Add to metadata
            metadata.append({
                "log_id": entry['log_id'],
                "file_path": str(log_file.relative_to(output_dir)),
                "platform": entry['platform'],
                "error_category": entry['error_category'],
                "build_number": entry['build_number'],
                "timestamp": entry['timestamp'],
            })
        
        # Save metadata CSV
        import csv
        csv_file = output_dir / "dataset.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=metadata[0].keys())
            writer.writeheader()
            writer.writerows(metadata)
        
        # Save JSON
        json_file = output_dir / "dataset.json"
        with open(json_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save statistics
        stats = {
            "total_logs": len(dataset),
            "platforms": {},
            "error_categories": {},
        }
        
        for entry in metadata:
            stats["platforms"][entry["platform"]] = stats["platforms"].get(entry["platform"], 0) + 1
            stats["error_categories"][entry["error_category"]] = stats["error_categories"].get(entry["error_category"], 0) + 1
        
        stats_file = output_dir / "statistics.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✅ Dataset saved to {output_dir}")
        print(f"📊 Total logs: {stats['total_logs']}")
        print(f"📁 Files:")
        print(f"   - {csv_file.name}")
        print(f"   - {json_file.name}")
        print(f"   - {stats_file.name}")
        print(f"   - logs/ ({len(dataset)} files)")
        print(f"\n📈 Distribution:")
        for category, count in sorted(stats["error_categories"].items()):
            print(f"   {category}: {count} ({count/len(dataset)*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic CI/CD log dataset")
    parser.add_argument("--output", "-o", type=str, default="data/synthetic_logs",
                        help="Output directory for dataset")
    parser.add_argument("--count", "-c", type=int, default=300,
                        help="Number of logs to generate")
    parser.add_argument("--seed", "-s", type=int, default=42,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    print("🚀 Generating synthetic CI/CD log dataset...")
    print(f"📊 Target count: {args.count}")
    print(f"🎲 Random seed: {args.seed}")
    print(f"📁 Output: {args.output}\n")
    
    generator = SyntheticLogGenerator(seed=args.seed)
    dataset = generator.generate_dataset(total_count=args.count)
    generator.save_dataset(dataset, Path(args.output))
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
