#!/usr/bin/env python3
"""
Dynamic Pre-commit Hook Generator

This script analyzes your codebase and generates customized pre-commit hooks
based on your project's specific needs. It can be run in interactive or
non-interactive mode.

Usage:
    python3 scripts/dynamic_precommit_generator.py
    python3 scripts/dynamic_precommit_generator.py --non-interactive
    python3 scripts/dynamic_precommit_generator.py --non-interactive --install
"""

import os
import sys
import yaml
import argparse
import subprocess
import glob
import hashlib
from typing import Dict, Any, Optional, List, Tuple
import json

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Default configuration if Gemini API is not available
DEFAULT_CONFIG = """repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
-   repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
    -   id: black
-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        args: [--count, --select=E9,F63,F7,F82, --show-source, --statistics]
    -   id: flake8
        name: flake8-complexity
        args: [--count, --exit-zero, --max-complexity=10, --max-line-length=127, --statistics]
-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.4.1
    hooks:
    -   id: mypy
        additional_dependencies: [
            "types-requests",
            "types-beautifulsoup4",
            "types-flask",
            "types-apispec",
            "types-marshmallow",
            "types-psutil",
        ]
-   repo: local
    hooks:
    -   id: check-doc-freshness
        name: Check Documentation Freshness
        entry: ./scripts/check_doc_freshness.py
        language: system
        pass_filenames: false
        always_run: true
        require_serial: true
        stages: [commit]

    -   id: check-precommit-hooks
        name: Check if pre-commit hooks need updating
        entry: python3 scripts/check_precommit_hooks.py
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit]
        verbose: true

    -   id: dependency-check
        name: dependency-check
        entry: python scripts/check_dependencies.py
        language: system
        pass_filenames: false
        always_run: true

    -   id: docker-verify
        name: docker-verify
        entry: scripts/verify_docker_build.sh
        language: system
        pass_filenames: false
        stages: [manual]
"""

def setup_gemini() -> Tuple[bool, Optional[str]]:
    """Set up the Gemini API client."""
    if not GENAI_AVAILABLE:
        return False, "google-generativeai package not installed"
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        return False, "GOOGLE_GEMINI_API_KEY not set"
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    return True, None

def analyze_codebase() -> Dict[str, Any]:
    """Analyze the codebase to identify file types, dependencies, etc."""
    result = {
        "file_types": [],
        "dependencies": [],
        "has_docker": False,
        "has_tests": False,
        "has_docs": False,
    }
    
    # Check file types
    for ext in [".py", ".md", ".yml", ".yaml", ".sh", ".ps1", ".toml"]:
        if glob.glob(f"**/*{ext}", recursive=True):
            result["file_types"].append(ext)
    
    # Check for dependencies
    if os.path.exists("setup.py"):
        result["has_setup_py"] = True
    if os.path.exists("requirements.txt"):
        result["has_requirements_txt"] = True
    if os.path.exists("pyproject.toml"):
        result["has_pyproject_toml"] = True
    
    # Check for Docker
    if os.path.exists("Dockerfile") or glob.glob("Dockerfile.*"):
        result["has_docker"] = True
    
    # Check for tests
    if os.path.exists("tests") or glob.glob("**/test_*.py", recursive=True):
        result["has_tests"] = True
    
    # Check for docs
    if os.path.exists("docs") or glob.glob("**/*.md", recursive=True):
        result["has_docs"] = True
    
    # Get current pre-commit config if it exists
    if os.path.exists(".pre-commit-config.yaml"):
        with open(".pre-commit-config.yaml", "r") as f:
            result["current_config"] = f.read()
    else:
        result["current_config"] = None
    
    return result

def analyze_cicd_workflows() -> Dict[str, Any]:
    """Analyze CI/CD workflows to ensure alignment."""
    result = {
        "has_github_actions": False,
        "workflows": [],
    }
    
    # Check for GitHub Actions
    if os.path.exists(".github/workflows"):
        result["has_github_actions"] = True
        for workflow_file in glob.glob(".github/workflows/*.yml"):
            with open(workflow_file, "r") as f:
                try:
                    workflow = yaml.safe_load(f)
                    result["workflows"].append({
                        "name": workflow.get("name", os.path.basename(workflow_file)),
                        "file": workflow_file,
                    })
                except yaml.YAMLError:
                    # If we can't parse the workflow, just record the file
                    result["workflows"].append({
                        "name": os.path.basename(workflow_file),
                        "file": workflow_file,
                    })
    
    return result

def generate_config_with_gemini(codebase_info: Dict[str, Any], cicd_info: Dict[str, Any]) -> Optional[str]:
    """Generate a pre-commit configuration using Gemini."""
    if not GENAI_AVAILABLE:
        return None
    
    # Set up the Gemini API
    gemini_available, error = setup_gemini()
    if not gemini_available:
        print(f"Warning: {error}")
        print("Falling back to default configuration")
        return None
    
    # Create a prompt for Gemini
    prompt = f"""
    Generate a pre-commit configuration for a Python project with the following characteristics:
    
    Codebase information:
    {json.dumps(codebase_info, indent=2)}
    
    CI/CD information:
    {json.dumps(cicd_info, indent=2)}
    
    The configuration should be in YAML format and include hooks for:
    1. Code formatting (black, isort)
    2. Linting (flake8)
    3. Type checking (mypy)
    4. Security checks (bandit)
    5. Custom hooks for checking documentation freshness
    6. Custom hooks for checking dependencies
    
    If the codebase has Docker, include a hook for verifying Docker builds.
    
    The configuration should be compatible with the CI/CD workflows.
    
    Return only the YAML configuration without any explanation.
    """
    
    try:
        # Generate the configuration
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Extract the YAML configuration
        config = response.text.strip()
        
        # Validate the YAML
        try:
            yaml.safe_load(config)
            return config
        except yaml.YAMLError:
            print("Warning: Generated configuration is not valid YAML")
            print("Falling back to default configuration")
            return None
    except Exception as e:
        print(f"Error generating configuration with Gemini: {e}")
        print("Falling back to default configuration")
        return None

def fallback_config(codebase_info: Dict[str, Any]) -> str:
    """Generate a fallback pre-commit configuration."""
    # If we have a current config, use that
    if codebase_info.get("current_config"):
        return codebase_info["current_config"]
    
    # Otherwise, use the default config
    return DEFAULT_CONFIG

def save_config(config: str) -> None:
    """Save the pre-commit configuration."""
    with open(".pre-commit-config.yaml", "w") as f:
        f.write(config)
    
    # Create the pre-commit hooks directory if it doesn't exist
    os.makedirs(".pre-commit-hooks", exist_ok=True)
    
    # Save the codebase signature
    signature = get_codebase_signature()
    with open(".pre-commit-hooks/codebase_signature.txt", "w") as f:
        f.write(signature)

def get_codebase_signature() -> str:
    """Generate a signature of the codebase based on key files."""
    signature = ""
    
    # Check Python files
    for py_file in sorted(glob.glob("**/*.py", recursive=True)):
        if "venv" not in py_file and ".git" not in py_file:
            file_hash = get_file_hash(py_file)
            if file_hash:
                signature += f"{py_file}:{file_hash}\n"
    
    # Check workflow files
    for workflow_file in sorted(glob.glob(".github/workflows/*.yml")):
        file_hash = get_file_hash(workflow_file)
        if file_hash:
            signature += f"{workflow_file}:{file_hash}\n"
    
    # Check setup files
    for setup_file in ["setup.py", "pyproject.toml", "requirements.txt"]:
        if os.path.exists(setup_file):
            file_hash = get_file_hash(setup_file)
            if file_hash:
                signature += f"{setup_file}:{file_hash}\n"
    
    return signature

def get_file_hash(file_path: str) -> Optional[str]:
    """Calculate the hash of a file."""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def install_hooks() -> None:
    """Install the pre-commit hooks."""
    try:
        subprocess.run(["pre-commit", "install"], check=True)
        print("Pre-commit hooks installed successfully")
    except subprocess.CalledProcessError:
        print("Error installing pre-commit hooks")
        print("Make sure pre-commit is installed: pip install pre-commit")
    except FileNotFoundError:
        print("pre-commit command not found")
        print("Install pre-commit: pip install pre-commit")

def main() -> int:
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate pre-commit hooks")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    parser.add_argument("--install", action="store_true", help="Install hooks after generating")
    args = parser.parse_args()
    
    print("Analyzing codebase...")
    codebase_info = analyze_codebase()
    
    print("Analyzing CI/CD workflows...")
    cicd_info = analyze_cicd_workflows()
    
    print("Generating pre-commit configuration...")
    config = generate_config_with_gemini(codebase_info, cicd_info)
    if not config:
        config = fallback_config(codebase_info)
    
    if not args.non_interactive:
        print("\nGenerated pre-commit configuration:")
        print("-----------------------------------")
        print(config)
        print("-----------------------------------")
        
        response = input("Do you want to save this configuration? (y/n) ")
        if response.lower() != "y":
            print("Configuration not saved")
            return 0
    
    print("Saving configuration...")
    save_config(config)
    
    if args.install:
        print("Installing hooks...")
        install_hooks()
    
    print("Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
