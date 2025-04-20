#!/usr/bin/env python3
"""
Script to check if pre-commit hooks need updating.

This script analyzes the codebase and determines if the pre-commit hooks
need to be updated based on changes to the codebase.

Returns:
    0 if hooks are up to date
    1 if hooks need updating
"""

import os
import sys
import yaml
import hashlib
import glob
from datetime import datetime, timedelta

def get_file_hash(file_path):
    """Calculate the hash of a file."""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_codebase_signature():
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

def check_hooks_freshness():
    """Check if the pre-commit hooks are fresh."""
    # Check if the pre-commit config exists
    if not os.path.exists(".pre-commit-config.yaml"):
        print("Pre-commit config does not exist. Hooks need updating.")
        return False
    
    # Check if the pre-commit hooks directory exists
    if not os.path.exists(".pre-commit-hooks"):
        os.makedirs(".pre-commit-hooks", exist_ok=True)
    
    # Check if the signature file exists
    signature_file = ".pre-commit-hooks/codebase_signature.txt"
    if not os.path.exists(signature_file):
        print("Codebase signature file does not exist. Hooks need updating.")
        return False
    
    # Check if the signature has changed
    current_signature = get_codebase_signature()
    with open(signature_file, 'r') as f:
        old_signature = f.read()
    
    if current_signature != old_signature:
        print("Codebase has changed. Hooks need updating.")
        return False
    
    # Check if the hooks are older than a week
    last_modified = datetime.fromtimestamp(os.path.getmtime(signature_file))
    if datetime.now() - last_modified > timedelta(days=7):
        print("Hooks are older than a week. Hooks need updating.")
        return False
    
    print("Hooks are up to date.")
    return True

def main():
    """Main function."""
    if check_hooks_freshness():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
