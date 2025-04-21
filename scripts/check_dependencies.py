#!/usr/bin/env python3
"""
Script to check for dependency version mismatches.
This script is used to ensure that the dependencies installed in the environment
match the expected versions, especially for critical dependencies like marshmallow.
"""

import sys
import importlib.metadata
import pkg_resources

# Define the minimum required versions for critical dependencies
REQUIRED_VERSIONS = {
    "marshmallow": "3.26.0",
    "apispec": "6.0.0",
    "flask": "2.0.0",
}

def check_dependency_versions():
    """Check if the installed dependencies meet the minimum version requirements."""
    errors = []
    
    for package, min_version in REQUIRED_VERSIONS.items():
        try:
            installed_version = importlib.metadata.version(package)
            if pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(min_version):
                errors.append(
                    f"{package}: installed version {installed_version} is less than required version {min_version}"
                )
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"{package}: not installed")
    
    return errors

def main():
    """Main function to check dependencies and exit with appropriate status code."""
    print("Checking dependency versions...")
    errors = check_dependency_versions()
    
    if errors:
        print("Dependency version check failed:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease update your dependencies to match the required versions.")
        sys.exit(1)
    
    print("All dependencies meet the minimum version requirements.")
    sys.exit(0)

if __name__ == "__main__":
    main()
