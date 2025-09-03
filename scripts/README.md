# Scripts Directory

This directory contains utility scripts for the project.

## Branch Synchronization Script

The `sync-branches.sh` script provides comprehensive branch synchronization capabilities between main and develop branches with conflict detection and resolution.

### Usage

```bash
# Check sync status (dry run)
./scripts/sync-branches.sh --dry-run main develop

# Sync with verbose output
./scripts/sync-branches.sh --verbose main develop

# Force sync despite conflicts (use with caution)
./scripts/sync-branches.sh --force main develop

# Check reverse sync status
./scripts/sync-branches.sh --dry-run develop main
```

### Options

- `-d, --dry-run`: Show what would be done without making changes
- `-f, --force`: Force synchronization even if conflicts exist
- `-v, --verbose`: Enable verbose output with commit details
- `-h, --help`: Show help message

### Features

- **Conflict Detection**: Uses `git merge-tree` to detect conflicts before merging
- **Dry Run Mode**: Safe testing without making actual changes
- **Verbose Output**: Detailed information about commits and changes
- **Force Sync**: Override conflicts when necessary (use with caution)
- **Colored Output**: Easy-to-read status messages with emojis
- **Logging**: Automatic logging to `logs/sync-branches.log`

### Integration

This script works in conjunction with the GitHub Actions workflows:
- `sync-main-to-develop.yml`: Automatic synchronization
- `auto-pr-develop-to-main.yml`: Automated pull request creation

See [BRANCH_SYNCHRONIZATION_STRATEGY.md](../BRANCH_SYNCHRONIZATION_STRATEGY.md) for complete documentation.

## Dynamic Pre-commit Hook Generator

The `dynamic_precommit_generator.py` script analyzes your CI/CD workflows and generates pre-commit hooks that match them. This ensures that checks that pass locally will also pass in CI.

### Usage

```bash
# Basic usage (interactive mode)
python scripts/dynamic_precommit_generator.py

# Non-interactive mode (for CI/CD)
python scripts/dynamic_precommit_generator.py --non-interactive

# Install hooks after generating
python scripts/dynamic_precommit_generator.py --install

# Force update even if no changes are detected
python scripts/dynamic_precommit_generator.py --force
```

### Requirements

The script requires the following dependencies:
- google-generativeai
- pyyaml
- python-dotenv

You can install them with:
```bash
pip install -r scripts/requirements-precommit-generator.txt
```

### Environment Variables

- `GOOGLE_GEMINI_API_KEY`: API key for Google's Gemini AI model. If not provided, the script will use fallback implementations.

### How It Works

1. The script analyzes your GitHub Actions workflows to identify CI/CD checks
2. It extracts parameters like line length, ignore rules, etc.
3. It generates a pre-commit configuration that matches those checks
4. It creates custom hooks as needed (e.g., documentation freshness checker)

## Pre-commit Hook Checker

The `check_precommit_hooks.py` script checks if your pre-commit hooks need updating based on recent changes to the codebase.

### Usage

```bash
python scripts/check_precommit_hooks.py
```

This script is automatically run as a pre-commit hook itself, so you'll be notified if your hooks need updating.

### Requirements

Same as the dynamic pre-commit hook generator.
