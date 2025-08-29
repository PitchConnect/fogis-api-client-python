# Contributing to PitchConnect Projects

Thank you for your interest in contributing to this project! This guide provides essential information to help you contribute effectively.

## Quick Start Workflow

Follow these steps to ensure your contributions work smoothly with our automation:

1. **Create a branch** from `develop` using the appropriate prefix:
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

2. **Create a draft PR** immediately after creating your branch:
   ```bash
   gh pr create --draft --base develop --title "Draft: Your feature title" --body "Fixes #123"
   ```
   > ⚠️ Creating a draft PR is critical for our automation to track work-in-progress!

3. **Reference the issue** in the PR description using keywords like "Fixes #123" or "Resolves #123"
   > This automatically tags the issue as "in-progress"

4. **Develop** your changes with frequent, small commits

5. **Run pre-commit hooks** before pushing:
   ```bash
   pre-commit run --all-files
   ```

6. **Push** your changes:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Switch from draft to ready** when your implementation is complete:
   ```bash
   gh pr ready
   ```
   > This triggers additional automation workflows

8. **Monitor CI/CD pipelines** after pushing changes:
   - If CI/CD fails:
     ```bash
     # Update local pre-commit hooks to match CI/CD
     ./update_precommit_hooks.sh
     # Fix issues and push again
     git push origin feature/your-feature-name
     ```
   - If CI/CD passes:
     > The PR will automatically be marked as ready for review

9. **Address review feedback** if requested

10. **Merge** after approval (maintainers will handle this)

## Branching Model

### Branch Structure

This project follows the GitFlow workflow:

- `main`: Production-ready code. Always stable and releasable.
- `develop`: Integration branch for features. Contains code for the next release.
- `feature/*`: New features or enhancements.
- `bugfix/*`: Bug fixes.
- `docs/*`: Documentation changes only.
- `refactor/*`: Code refactoring without changing functionality.
- `test/*`: Adding or updating tests.
- `release/*`: Release preparation branches.
- `hotfix/*`: Emergency fixes for production issues.

### Branch Protection

- **Never Push Directly to Main or Develop**
  - All changes must go through pull requests
  - This ensures code quality and prevents accidental breaking changes

### Branch Naming Convention

- `feature/descriptive-name` for new features (branch from develop)
- `bugfix/issue-description` for bug fixes (branch from develop)
- `docs/what-is-documented` for documentation changes (branch from develop)
- `refactor/what-is-refactored` for code refactoring (branch from develop)
- `test/what-is-tested` for adding or updating tests (branch from develop)
- `release/x.y.z` for release preparation (branch from develop)
- `hotfix/issue-description` for urgent production fixes (branch from main)

## Working with Issues and PRs

### Creating Branches for Issues

- When starting work on an issue, create a draft PR immediately
- Reference the issue in the PR description using keywords like "Fixes #123"
- This ensures the issue is properly tracked as in-progress
- The issue will automatically be labeled as "in-progress"

### Branch Cleanup

- Delete your branches after they've been merged
- Use `git branch -d branch-name` for local branch deletion
- Use `git push origin --delete branch-name` for remote branch deletion

### Issue References in Commits

- Reference issues in commit messages when applicable
- Format: `Type: Short description (fixes #123)`
- This creates a link between the commit and the issue

## Code Standards

- Follow language-specific style guides (PEP 8 for Python, ESLint for JavaScript)
- Write clear, descriptive commit messages
- Include tests for new features and bug fixes
- Document public APIs and complex logic
- Run pre-commit hooks before pushing changes

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality. If hooks fail in CI but pass locally:

```bash
# Update hooks to match CI/CD
./update_precommit_hooks.sh

# Reinstall if needed
pre-commit uninstall
pre-commit install
```

## Pull Request Guidelines

- Use clear, descriptive titles
- Reference related issues
- Fill out the PR template completely
- Keep PRs focused on a single concern
- Respond promptly to review comments

## Working with AI Assistants

When using AI tools (GitHub Copilot, Claude, ChatGPT, etc.):

1. **Instruct the AI** to follow these contribution guidelines
2. **Review AI-generated code** carefully before committing
3. **Ensure AI follows the workflow** steps above, especially creating draft PRs
4. **Verify AI-generated code** passes all tests and pre-commit hooks

## Issue Management

- Use descriptive titles that clearly state the problem or feature
- Include detailed descriptions with context and requirements
- Add appropriate labels
- Reference related issues or PRs

## Repository-Specific Guidelines

### Testing in fogis_api_client

#### Running Tests

Before submitting a pull request, please ensure all tests pass:

1. **Run unit tests**:
   ```bash
   python -m unittest discover tests
   ```

2. **Run integration tests**:
   ```bash
   python -m pytest integration_tests
   ```

3. **When adding new features or modifying existing ones**:
   - Add or update unit tests in the `tests/` directory
   - Add or update integration tests in the `integration_tests/` directory
   - Ensure test coverage for both success and error cases

#### Using the Mock Server for Testing

The mock server provides a simulated FOGIS API environment for development and testing without requiring real credentials:

1. **Install the mock server dependencies**:
   ```bash
   pip install -e ".[dev,mock-server]"
   ```

2. **Start the mock server**:
   ```bash
   python -m fogis_api_client.cli.mock_server start
   ```

3. **Run integration tests against the mock server**:
   ```bash
   python -m pytest integration_tests
   ```

4. **Stop the mock server when you're done**:
   ```bash
   python -m fogis_api_client.cli.mock_server stop
   ```

#### Running Integration Tests with the Mock Server (recommended)

To run the full integration test suite reliably without external dependencies, use the provided helper script. It automatically starts the mock server (if not already running), uses the current Python interpreter (sys.executable), and excludes external API endpoint tests by default.

- Run all integration tests against the mock server (excluding external api_endpoints):
  ```bash
  python3 scripts/run_integration_tests_with_mock.py
  ```

- Increase verbosity:
  ```bash
  python3 scripts/run_integration_tests_with_mock.py -v
  ```

- Run a specific integration test file:
  ```bash
  python3 scripts/run_integration_tests_with_mock.py --test-file integration_tests/test_cli.py
  ```

- Run a specific test by name (pattern):
  ```bash
  python3 scripts/run_integration_tests_with_mock.py --test-name TestCli::test_status_command
  ```

Notes:
- The script excludes tests marked as `api_endpoints` by default when running with the mock server. Those tests expect access to an external service and are not suitable for offline/mock runs.
- You can still run tests directly with pytest if preferred; ensure the mock server is running and consider `-k 'not api_endpoints'` to skip external endpoint tests.

5. **When adding new API endpoints**:

#### Running Integration Tests with the Mock Server (recommended)

To run the full integration test suite reliably without external dependencies, use the provided helper script. It automatically starts the mock server (if not already running), uses the current Python interpreter (sys.executable), and excludes external API endpoint tests by default.

- Run all integration tests against the mock server (excluding external api_endpoints):
  ```bash
  python3 scripts/run_integration_tests_with_mock.py
  ```

- Increase verbosity:
  ```bash
  python3 scripts/run_integration_tests_with_mock.py -v
  ```

- Run a specific integration test file:
  ```bash
  python3 scripts/run_integration_tests_with_mock.py --test-file integration_tests/test_cli.py
  ```

- Run a specific test by name (pattern):
  ```bash
  python3 scripts/run_integration_tests_with_mock.py --test-name TestCli::test_status_command
  ```

Notes:
- The script excludes tests marked as `api_endpoints` by default when running with the mock server. Those tests expect access to an external service and are not suitable for offline/mock runs.
- You can still run tests directly with pytest if preferred; ensure the mock server is running and consider `-k 'not api_endpoints'` to skip external endpoint tests.

   python -m fogis_api_client.cli.mock_server stop
   ```

5. **When adding new API endpoints**:
   - Add the endpoint to the mock server in `integration_tests/mock_fogis_server.py`
   - Add a request schema in `integration_tests/schemas/` for validation
   - Add integration tests that use the mock server
   - See the [Mock Server Documentation](docs/mock_server.md) for details

6. **Using the mock server in CI/CD**:
   - The GitHub Actions workflows are configured to use the mock server
   - Integration tests automatically start and stop the mock server
   - Use the `mock_api_urls` fixture in your tests to handle URL configuration

### Dynamic Pre-commit Hook Generator

This project uses a dynamic pre-commit hook generator powered by Google's Gemini LLM:

```bash
# Generate pre-commit hooks interactively
python3 scripts/dynamic_precommit_generator.py

# Generate pre-commit hooks non-interactively
python3 scripts/dynamic_precommit_generator.py --non-interactive

# Generate and install pre-commit hooks
python3 scripts/dynamic_precommit_generator.py --non-interactive --install
```

See `scripts/README_DYNAMIC_HOOKS.md` for more information.

<!-- END COMMON SECTION -->

## For Maintainers

The following guidelines are primarily for repository maintainers:

### Stale Branch Management

- Periodically review and clean up old branches
- Consider deleting branches that haven't been updated in 3+ months
- Before deleting, check if the branch contains unique work
- If a branch contains valuable work, create an issue to track it

### Abandoned PR Handling

- If a PR is abandoned, comment asking for status
- After 2 weeks without response, consider closing the PR
- Mention that the work can be continued in a new PR if needed

### Issue Status Automation

- When a draft PR is created: Issue status → "in-progress"
- When PR is marked as ready for review: Issue status → "review-ready"
- When PR is merged: Issue status → "merged-to-develop"
- When PR is closed without merging: Remove "in-progress" label and add a comment explaining why

Thank you for contributing!
