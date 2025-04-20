#!/usr/bin/env python3
"""
Test script for the dynamic pre-commit hook generator.

This script tests various aspects of the generator to ensure it works as expected.
"""
import os
import sys
import tempfile
import shutil
import subprocess
import yaml

# Add the parent directory to the path so we can import the generator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.dynamic_precommit_generator import (
    analyze_codebase,
    analyze_cicd_workflows,
    fallback_config,
    setup_gemini,
)

def test_analyze_codebase():
    """Test the analyze_codebase function."""
    print("Testing analyze_codebase...")
    
    # Run the analysis
    analysis = analyze_codebase()
    
    # Check that the analysis contains the expected keys
    expected_keys = ["file_extensions", "dependencies", "linting_configs", "current_config"]
    for key in expected_keys:
        if key not in analysis:
            print(f"❌ analyze_codebase: Missing key '{key}'")
            return False
    
    # Check that file_extensions is a list
    if not isinstance(analysis["file_extensions"], list):
        print(f"❌ analyze_codebase: file_extensions is not a list")
        return False
    
    # Check that dependencies is a list
    if not isinstance(analysis["dependencies"], list):
        print(f"❌ analyze_codebase: dependencies is not a list")
        return False
    
    print("✅ analyze_codebase: All checks passed")
    return True

def test_analyze_cicd_workflows():
    """Test the analyze_cicd_workflows function."""
    print("Testing analyze_cicd_workflows...")
    
    # Run the analysis
    cicd_checks = analyze_cicd_workflows()
    
    # Check that cicd_checks is a list
    if not isinstance(cicd_checks, list):
        print(f"❌ analyze_cicd_workflows: cicd_checks is not a list")
        return False
    
    print("✅ analyze_cicd_workflows: All checks passed")
    return True

def test_fallback_config():
    """Test the fallback_config function."""
    print("Testing fallback_config...")
    
    # Test with no current config
    config = fallback_config({"current_config": None})
    
    # Check that config is a string
    if not isinstance(config, str):
        print(f"❌ fallback_config: config is not a string")
        return False
    
    # Check that config is valid YAML
    try:
        yaml.safe_load(config)
    except yaml.YAMLError as e:
        print(f"❌ fallback_config: config is not valid YAML: {e}")
        return False
    
    # Test with current config
    current_config = "repos:\n- repo: local\n  hooks:\n  - id: test\n    name: test\n    entry: echo test\n    language: system"
    config = fallback_config({"current_config": current_config})
    
    # Check that config is the same as current_config
    if config != current_config:
        print(f"❌ fallback_config: config is not the same as current_config")
        return False
    
    print("✅ fallback_config: All checks passed")
    return True

def test_setup_gemini():
    """Test the setup_gemini function."""
    print("Testing setup_gemini...")
    
    # Check if API key is set
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("⚠️ setup_gemini: GOOGLE_GEMINI_API_KEY not set, skipping test")
        return True
    
    # Run setup_gemini
    model = setup_gemini()
    
    # Check that model is not None
    if model is None:
        print(f"❌ setup_gemini: model is None")
        return False
    
    print("✅ setup_gemini: All checks passed")
    return True

def test_non_interactive_mode():
    """Test the non-interactive mode."""
    print("Testing non-interactive mode...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy the current directory to the temporary directory
        for item in os.listdir("."):
            if item != ".git" and not item.startswith("."):
                src = os.path.join(".", item)
                dst = os.path.join(temp_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        # Run the generator in non-interactive mode
        result = subprocess.run(
            ["python3", "scripts/dynamic_precommit_generator.py", "--non-interactive"],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )
        
        # Check that the command succeeded
        if result.returncode != 0:
            print(f"❌ non_interactive_mode: Command failed with code {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
        
        # Check that the pre-commit config was created
        if not os.path.exists(os.path.join(temp_dir, ".pre-commit-config.yaml")):
            print(f"❌ non_interactive_mode: .pre-commit-config.yaml was not created")
            return False
        
        # Check that the pre-commit config is valid YAML
        with open(os.path.join(temp_dir, ".pre-commit-config.yaml"), "r") as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"❌ non_interactive_mode: .pre-commit-config.yaml is not valid YAML: {e}")
                return False
    
    print("✅ non_interactive_mode: All checks passed")
    return True

def main():
    """Run all tests."""
    print("Running tests for dynamic pre-commit hook generator...")
    print("====================================================")
    
    tests = [
        test_analyze_codebase,
        test_analyze_cicd_workflows,
        test_fallback_config,
        test_setup_gemini,
        test_non_interactive_mode,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\nTest results:")
    print(f"✅ {passed} tests passed")
    print(f"❌ {failed} tests failed")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
