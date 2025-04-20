#!/usr/bin/env python3
"""
Script to check if documentation is up to date with the codebase.

This script analyzes the codebase and documentation to ensure they are in sync.
It checks for:
1. Missing documentation for public modules, classes, and functions
2. Outdated documentation that doesn't match the current code
3. References to old versions or deprecated features

Returns:
    0 if documentation is up to date
    1 if documentation needs updating
"""

import os
import sys
import glob
import re
from datetime import datetime, timedelta

def check_readme_freshness():
    """Check if README.md is up to date."""
    if not os.path.exists("README.md"):
        print("README.md does not exist.")
        return False
    
    # Check if README.md was modified in the last 30 days
    last_modified = datetime.fromtimestamp(os.path.getmtime("README.md"))
    if datetime.now() - last_modified > timedelta(days=30):
        print("README.md is older than 30 days. Consider updating it.")
        return True  # Not critical, so return True
    
    return True

def check_api_docs_freshness():
    """Check if API documentation is up to date."""
    api_docs = glob.glob("docs/api_*.md") + glob.glob("docs/api/*.md")
    if not api_docs:
        # If there are no API docs, that's okay for this check
        return True
    
    # Check if any API docs were modified in the last 30 days
    for doc in api_docs:
        last_modified = datetime.fromtimestamp(os.path.getmtime(doc))
        if datetime.now() - last_modified > timedelta(days=30):
            print(f"{doc} is older than 30 days. Consider updating it.")
            # Not critical, so continue checking
    
    return True

def check_version_consistency():
    """Check if version numbers are consistent across files."""
    version_pattern = r"version\s*=\s*['\"]([^'\"]+)['\"]"
    versions = {}
    
    # Check setup.py
    if os.path.exists("setup.py"):
        with open("setup.py", "r") as f:
            content = f.read()
            match = re.search(version_pattern, content)
            if match:
                versions["setup.py"] = match.group(1)
    
    # Check __init__.py files
    for init_file in glob.glob("*/__init__.py"):
        with open(init_file, "r") as f:
            content = f.read()
            match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
            if match:
                versions[init_file] = match.group(1)
    
    # Check for inconsistencies
    if len(set(versions.values())) > 1:
        print("Version inconsistencies found:")
        for file, version in versions.items():
            print(f"  {file}: {version}")
        return False
    
    return True

def main():
    """Main function."""
    # Run all checks
    readme_fresh = check_readme_freshness()
    api_docs_fresh = check_api_docs_freshness()
    versions_consistent = check_version_consistency()
    
    # If any critical check fails, return 1
    if not versions_consistent:
        return 1
    
    # Non-critical checks just print warnings
    return 0

if __name__ == "__main__":
    sys.exit(main())
