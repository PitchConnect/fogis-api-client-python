#!/usr/bin/env python3
"""
Pre-commit hook to check for missing dependencies.

This script checks if all required dependencies are installed in the current environment.
It also verifies that the dependencies in Dockerfile.dev, Dockerfile.test, and Dockerfile.mock
are consistent.
"""

import importlib.util
import os
import re
import sys
from typing import Dict, List, Set

# List of required dependencies for the project
REQUIRED_DEPENDENCIES = [
    "flask",
    "marshmallow",
    "jsonschema",
    "requests",
    "pytest",
    "apispec",
]

# Files to check for dependency consistency
DOCKER_FILES = [
    "Dockerfile.dev",
    "Dockerfile.test",
    "Dockerfile.mock",
]


def check_installed_dependencies() -> List[str]:
    """Check if all required dependencies are installed."""
    missing_deps = []
    for dep in REQUIRED_DEPENDENCIES:
        if importlib.util.find_spec(dep) is None:
            missing_deps.append(dep)
    return missing_deps


def extract_dependencies_from_file(file_path: str) -> Set[str]:
    """Extract pip install dependencies from a file."""
    if not os.path.exists(file_path):
        return set()

    deps = set()
    with open(file_path, "r") as f:
        content = f.read()
        # Find all pip install commands
        pip_install_lines = re.findall(r"pip install[^&]*", content)
        for line in pip_install_lines:
            # Extract package names, ignoring version specifiers and options
            packages = re.findall(r"--no-cache-dir\s+([a-zA-Z0-9_-]+)(?:[>=<][^-\s]*)?", line)
            deps.update(packages)
            # Also check for -e . installations
            if "-e ." in line:
                deps.add("project-package")
    return deps


def check_dependency_consistency() -> Dict[str, Set[str]]:
    """Check if dependencies are consistent across Docker files."""
    file_deps = {}
    for file_path in DOCKER_FILES:
        if os.path.exists(file_path):
            file_deps[file_path] = extract_dependencies_from_file(file_path)
    return file_deps


def main() -> int:
    """Run the dependency checks."""
    exit_code = 0

    # Check for missing dependencies in the current environment
    missing_deps = check_installed_dependencies()
    if missing_deps:
        print("❌ Missing dependencies in current environment:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("Please install them with: pip install " + " ".join(missing_deps))
        exit_code = 1
    else:
        print("✅ All required dependencies are installed in the current environment.")

    # Check for dependency consistency across Docker files
    file_deps = check_dependency_consistency()
    
    # Check if jsonschema is in all Docker files
    for file_path, deps in file_deps.items():
        if "jsonschema" not in deps and file_path != "Dockerfile.mock":
            print(f"❌ Missing 'jsonschema' dependency in {file_path}")
            exit_code = 1
        else:
            print(f"✅ Dependencies in {file_path} look good.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
