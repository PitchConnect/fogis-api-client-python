# Contributing to PitchConnect Projects

<!-- START COMMON SECTION v1.0 (Last updated: 2023-05-02) -->

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
  - [Branching Model](#branching-model)
  - [Feature Development](#feature-development)
  - [Bug Fixes](#bug-fixes)
  - [Releases](#releases)
  - [Hotfixes](#hotfixes)
- [Pull Request Process](#pull-request-process)
  - [Creating a Pull Request](#creating-a-pull-request)
  - [PR Review Process](#pr-review-process)
  - [Merging Guidelines](#merging-guidelines)
- [Coding Standards](#coding-standards)
  - [General Guidelines](#general-guidelines)
  - [Language-Specific Guidelines](#language-specific-guidelines)
  - [Documentation](#documentation)
  - [Testing](#testing)
- [Working with AI Assistants](#working-with-ai-assistants)
  - [When to Use AI Assistance](#when-to-use-ai-assistance)
  - [Best Practices](#best-practices)
  - [Implementation Challenges for AI Agents](#ai-implementation-challenges)
  - [GitHub CLI Usage](#github-cli-usage)- [Pre-commit Hooks](#pre-commit-hooks)
  - [Installation](#precommit-installation)
  - [Usage](#precommit-usage)
  - [Common Hook Failures and Solutions](#precommit-failures)
  - [Aligning Pre-commit Hooks with CI/CD](#precommit-cicd)  - [Best Practices](#best-practices)
  - [GitHub CLI Usage](#github-cli-usage)
- [Issue Lifecycle and Automation](#issue-lifecycle-and-automation)
  - [Issue Status Automation](#issue-status-automation)
  - [Referencing Issues in PRs](#referencing-issues-in-prs)
  - [Manual Issue Closure](#manual-issue-closure)
- [Work in Progress](#work-in-progress)
- [Repository-Specific Guidelines](#repository-specific-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by the [PitchConnect Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the repository maintainers.

## Getting Started

To get started contributing to this project:

1. Fork the repository
2. Clone your fork: `gh repo clone your-username/repo-name`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dependencies according to the project's README
5. Make your changes
6. Run tests to ensure your changes don't break existing functionality
7. Commit your changes with descriptive commit messages
8. Push to your branch: `git push origin feature/your-feature-name`
9. Create a Pull Request

## Development Workflow

<a id="branching-model"></a>
### Branching Model

This project follows the GitFlow workflow:

- `main`: Production-ready code
- `develop`: Latest development changes
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `release/*`: Release preparation
- `hotfix/*`: Urgent fixes for production

<a id="feature-development"></a>
### Feature Development

1. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

2. Implement your changes, committing regularly with descriptive messages
3. Push your branch to GitHub:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Create a Pull Request to merge into `develop`
5. Address review feedback
6. Once approved, merge into `develop`

<a id="bug-fixes"></a>
### Bug Fixes

1. Create a bugfix branch from `develop`:
   ```bash
   git checkout develop
   git pull
   git checkout -b bugfix/bug-description
   ```

2. Fix the bug, adding tests to prevent regression
3. Push your branch to GitHub:
   ```bash
   git push -u origin bugfix/bug-description
   ```

4. Create a Pull Request to merge into `develop`
5. Once approved, merge into `develop`

<a id="releases"></a>
### Releases

1. Create a release branch from `develop`:
   ```bash
   git checkout develop
   git pull
   git checkout -b release/v1.2.3
   ```

2. Make any final adjustments and version bumps
3. Create a Pull Request to merge into `main`
4. Once approved, merge into `main`
5. Tag the release:
   ```bash
   git checkout main
   git pull
   git tag -a v1.2.3 -m "Release v1.2.3"
   git push origin v1.2.3
   ```

6. Merge `main` back into `develop`:
   ```bash
   git checkout develop
   git merge main
   git push
   ```

<a id="hotfixes"></a>
### Hotfixes

1. Create a hotfix branch from `main`:
   ```bash
   git checkout main
   git pull
   git checkout -b hotfix/critical-bug-fix
   ```

2. Fix the critical bug
3. Create a Pull Request to merge into `main`
4. Once approved, merge into `main`
5. Tag the hotfix:
   ```bash
   git checkout main
   git pull
   git tag -a v1.2.4 -m "Hotfix v1.2.4"
   git push origin v1.2.4
   ```

6. Merge `main` back into `develop`:
   ```bash
   git checkout develop
   git merge main
   git push
   ```

## Pull Request Process

<a id="creating-a-pull-request"></a>
### Creating a Pull Request

1. Ensure your code passes all tests and linting
2. Update documentation to reflect any changes
3. Create a Pull Request with a clear title and description
4. Reference any related issues using keywords like "Fixes #123"
5. Add appropriate labels
6. Request reviews from relevant team members

<a id="pr-review-process"></a>
### PR Review Process

1. Reviewers will check for:
   - Code quality and correctness
   - Test coverage
   - Documentation
   - Adherence to coding standards
   - Potential side effects

2. Address all review comments
3. Once approved, the PR can be merged

<a id="merging-guidelines"></a>
### Merging Guidelines

- Feature and bugfix branches should be merged into `develop` using squash merge
- Release branches should be merged into `main` using a regular merge (no squash)
- Hotfix branches should be merged into both `main` and `develop` using a regular merge

## Coding Standards

<a id="general-guidelines"></a>
### General Guidelines

- Write clean, readable, and maintainable code
- Follow the principle of "Don't Repeat Yourself" (DRY)
- Keep functions and methods small and focused
- Use meaningful variable and function names
- Add comments for complex logic, but prefer self-documenting code
- Follow the project's existing code style

<a id="language-specific-guidelines"></a>
### Language-Specific Guidelines

#### Python
- Follow PEP 8 style guide
- Use type hints where appropriate
- Use docstrings for functions and classes
- Use virtual environments for dependency management

#### JavaScript/TypeScript
- Follow ESLint configuration
- Use modern ES6+ features
- Prefer async/await over callbacks
- Use TypeScript types/interfaces

#### Other Languages
- Follow the established conventions for the language
- Consult language-specific style guides

<a id="documentation"></a>
### Documentation

- Keep README.md up to date
- Document public APIs
- Include examples where helpful
- Update documentation when making changes
- Use clear and concise language

<a id="testing"></a>
### Testing

- Write unit tests for new functionality
- Ensure existing tests pass
## Pre-commit Hooks

Pre-commit hooks are an essential tool for catching issues before they are committed to the repository. Using pre-commit hooks is **mandatory** for all contributors, including AI agents.

<a id="precommit-installation"></a>
### Installation

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the hooks for the repository:
   ```bash
   pre-commit install
   ```

3. Verify the installation:
   ```bash
   pre-commit --version
   ```

<a id="precommit-usage"></a>
### Usage

Always run pre-commit hooks before creating a PR:

1. Run pre-commit on all files:
   ```bash
   pre-commit run --all-files
   ```

2. If hooks modify files:
   - Review the changes
   - Stage the modified files: `git add .`
   - Run pre-commit again to ensure all checks pass

3. Only commit your changes after all pre-commit hooks pass

<a id="precommit-failures"></a>
### Common Hook Failures and Solutions

| Hook | Error Message | Solution |
|------|---------------|----------|
| black | "would reformat file.py" | Let the hook fix it or run `black file.py` |
| flake8 | "line too long" | Break the line into multiple lines |
| isort | "would sort imports" | Let the hook fix it or run `isort file.py` |
| trailing-whitespace | "trailing whitespace" | Let the hook fix it |
| end-of-file-fixer | "no newline at end of file" | Let the hook fix it |

<a id="precommit-cicd"></a>
### Aligning Pre-commit Hooks with CI/CD

If the CI/CD pipeline catches issues that weren't detected by pre-commit hooks:

1. This indicates a **process problem** that needs fixing
2. Open an issue with the "pre-commit" and "ci-cd" labels
3. Suggest updates to the pre-commit configuration to catch similar issues in the future

Example issue report:
```
Title: Align pre-commit hooks with CI flake8 settings

Description:
The CI pipeline caught a flake8 error about line length that wasn't caught by pre-commit hooks.
The CI is using max-line-length=88 while our pre-commit config uses max-line-length=100.

Suggested fix:
Update .pre-commit-config.yaml to match CI settings:
```yaml
- repo: https://github.com/pycqa/flake8
  rev: 6.0.0
  hooks:
    - id: flake8
      args: [--max-line-length=88]
```
```

This feedback loop is essential for continuous improvement of our development process.
- Aim for high test coverage
- Include integration tests where appropriate
- Test edge cases and error conditions

## Working with AI Assistants

<a id="when-to-use-ai-assistance"></a>
### When to Use AI Assistance

AI assistants can be helpful for:
- Generating boilerplate code
- Explaining complex code
- Debugging issues
- Writing tests
- Documenting code
- Suggesting refactoring approaches

<a id="best-practices"></a>
### Best Practices

When working with AI assistants:

1. **Review all generated code** thoroughly before committing
2. **Understand the code** before using it
3. **Test generated code** rigorously
4. **Always run pre-commit hooks** on AI-generated code
5. **Update pre-commit hooks** if CI/CD catches issues that should have been caught locally4. **Provide clear instructions** to get better results
5. **Break down complex tasks** into smaller chunks
6. **Check for security issues** in generated code
7. **Verify licensing compatibility** of suggested solutions
8. **Read all comments** on issues and PRs, not just the initial description

<a id="github-cli-usage"></a>
### GitHub CLI Usage
<a id="ai-implementation-challenges"></a>
### Implementation Challenges for AI Agents

AI agents may encounter specific challenges when implementing code changes or working with repositories. This section documents common challenges and provides solutions to minimize the need for human intervention.

#### File Editing Challenges

When editing large files or making complex changes:

1. **Challenge**: Direct editing of large files can be error-prone
   - **Solution**: Use a temporary file approach:
     ```bash
     # Save original file to temp location
     cat original_file.md > /tmp/temp_file.md
     
     # Edit the temp file (using sed, awk, etc.)
     sed -i '' 's/old text/new text/g' /tmp/temp_file.md
     
     # Copy back to original location
     cp /tmp/temp_file.md original_file.md
     ```

2. **Challenge**: Complex replacements with special characters
   - **Solution**: Use delimiter characters that don't appear in your text:
     ```bash
     # Using | as delimiter instead of / when text contains slashes
     sed -i '' 's|http://example.com|https://example.com|g' file.md
     ```

3. **Challenge**: Finding the right line numbers for targeted edits
   - **Solution**: Use grep with line numbers to locate insertion points:
     ```bash
     grep -n "## Section Title" file.md
     ```

#### Command Line Tool Limitations

When working with command-line tools like `gh`:

1. **Challenge**: Commands failing silently or with unclear errors
   - **Solution**: Add explicit error checking and verbose flags:
     ```bash
     # Use verbose mode when available
     gh pr create --verbose [other options]
     
     # Check return codes
     if [ $? -ne 0 ]; then
       echo "Command failed, trying alternative approach"
       # Alternative approach here
     fi
     ```

2. **Challenge**: Context switching between different tools
   - **Solution**: Minimize tool switching by batching similar operations:
     ```bash
     # Batch all gh operations together
     gh repo clone repo1
     gh repo clone repo2
     
     # Then batch all git operations
     cd repo1 && git checkout -b feature/new-feature
     cd ../repo2 && git checkout -b feature/new-feature
     ```

3. **Challenge**: Handling repository-specific configurations
   - **Solution**: Check for configuration files before executing commands:
     ```bash
     # Check if pre-commit is configured
     if [ -f .pre-commit-config.yaml ]; then
       pre-commit run --all-files
     else
       echo "No pre-commit configuration found"
     fi
     ```

#### GitHub Actions Testing

When implementing or modifying GitHub Actions:

1. **Challenge**: Difficulty verifying if actions are working correctly
   - **Solution**: Create a test workflow file with explicit logging:
     ```yaml
     name: Test Workflow
     on: [push]
     jobs:
       test:
         runs-on: ubuntu-latest
         steps:
           - name: Debug Info
             run: |
               echo "Event name: ${{ github.event_name }}"
               echo "Event payload: ${{ toJSON(github.event) }}"
           - name: Test Step
             run: echo "This is a test"
     ```

2. **Challenge**: Actions requiring specific permissions
   - **Solution**: Explicitly define required permissions in the workflow:
     ```yaml
     permissions:
       issues: write
       pull-requests: write
       contents: read
     ```

3. **Challenge**: Triggering actions for testing
   - **Solution**: Use the `workflow_dispatch` event for manual testing:
     ```yaml
     on:
       workflow_dispatch:
         inputs:
           test-param:
             description: 'Test parameter'
             required: true
             default: 'test'
     ```

By documenting these challenges and solutions, we aim to reduce context switching and the need for human intervention when AI agents are implementing changes.

AI agents should use GitHub CLI (gh) for GitHub operations whenever possible. This provides a consistent interface and reduces the need for web browser interactions.

#### Common Commands

- Clone a repository: `gh repo clone PitchConnect/repo-name`
- Create an issue: `gh issue create --title "Issue title" --body-file issue.md`
- Create a PR: `gh pr create --title "PR title" --body-file pr.md`
- Check PR status: `gh pr status`
- Review a PR: `gh pr checkout {pr-number}`
- List issues: `gh issue list --state open`

#### Best Practices

- Always clean up temporary files after use
- Use `--body-file` instead of inline content for complex markdown
- Reference issues in PRs using the appropriate syntax

## Issue Lifecycle and Automation

<a id="standardized-labels"></a>
### Standardized Labels

This project uses a standardized set of labels across all repositories to ensure consistency and clarity:

#### Status Labels
- `triage` - Needs initial review by maintainers (removed after triage)
- `ready-for-development` - Triaged and ready for someone to work on
- `in-progress` - Being worked on in a draft PR
- `review-ready` - Work complete and ready for review
- `merged-to-develop` - Merged to develop branch
- `released` - Released to production

#### Type Labels
- `bug` - Something isn't working as expected
- `enhancement` - New feature or improvement
- `documentation` - Documentation changes
- `refactor` - Code changes that neither fix a bug nor add a feature
- `test` - Adding or improving tests

#### Priority Labels
- `priority:high` - Urgent, needs immediate attention
- `priority:medium` - Important but not urgent
- `priority:low` - Nice to have, can wait

#### Complexity Labels
- `complexity:easy` - Good for beginners, small scope
- `complexity:medium` - Moderate difficulty, average scope
- `complexity:hard` - Complex changes, large scope

#### Additional Labels
- `good-first-issue` - Good for newcomers to the project
- `help-wanted` - Extra attention needed, looking for contributors
- `blocked` - Blocked by another issue or external factor
- `discussion` - Needs further discussion before work begins
- `wontfix` - This will not be worked on

<a id="issue-status-automation"></a>
### Issue Status Automation

This project uses automation to track issue status through the development lifecycle:

1. **When an issue is created**:
   - It will automatically be labeled as `triage`
   - Maintainers should review the issue and add appropriate type, priority, and complexity labels
   - After triage, maintainers should remove the `triage` label and add the `ready-for-development` label

2. **When you create a Draft PR**:
   - Referenced issues will automatically have the `ready-for-development` label removed
   - Issues will be labeled as `in-progress`
   - A comment will be added to the issue linking to your PR

3. **When you mark a PR as Ready for Review**:
   - The `in-progress` label will be removed
   - Issues will be labeled as `review-ready`

4. **When your PR is merged to `develop`**:
   - The `review-ready` label will be removed
   - Issues will be labeled as `merged-to-develop`
   - Issues will NOT be closed automatically at this stage
   - DO NOT manually close issues when merging to develop

5. **When a release is created**:
   - All `merged-to-develop` issues will be automatically included in the release PR
   - When the release is merged to `main`, the `merged-to-develop` label will be removed
   - Issues will receive a `released` label
   - Issues will be automatically closed
   - Issues will receive a `released` label

<a id="referencing-issues-in-prs"></a>
### Referencing Issues in PRs

Always reference issues in your PR using one of these keywords:
- `Fixes #123`
- `Resolves #123`
- `Closes #123`

Example PR description:
```
This PR adds user authentication via OAuth.

Fixes #123
```

This ensures the automation can properly track which issues are addressed by your PR.

<a id="manual-issue-closure"></a>
### Manual Issue Closure

Do not manually close issues when merging to develop. Issues should remain open until they are released to production (merged to main).

If you need to close an issue without a PR (e.g., duplicate, won't fix), add a comment explaining why.

## Work in Progress

When your work is not yet ready for review:

1. Create a **Draft Pull Request** instead of a regular PR
   - Use the dropdown menu next to "Create Pull Request" to select "Create Draft Pull Request"
   - This clearly indicates your PR is a work in progress
   - The PR cannot be merged until you mark it as ready for review

2. **IMPORTANT**: Do not mark a PR as ready for review until:
   - All CI/CD checks are passing
   - All pre-commit hooks have been run successfully
   - You have addressed any automated feedback
   - The code is fully ready for human review

3. When your work is complete and all checks pass:
   - Click "Ready for Review" to convert the Draft PR to a regular PR
   - This signals to reviewers that your work is ready for their attention

### CI/CD Pipeline Failures

If your PR fails CI/CD checks:

1. Review the failure logs carefully
2. Fix the issues in your branch
3. Push the changes to update the PR
4. Verify that all checks pass before marking as ready for review
5. If the CI/CD caught issues that should have been caught by pre-commit hooks, update the pre-commit configuration as well

Draft PRs are preferred over other methods like "WIP" in titles or special branches, as they provide a standard, built-in way to indicate work in progress.

## Repository-Specific Guidelines

Please refer to the repository-specific section below for any additional guidelines specific to this project.

<!-- END COMMON SECTION -->

## Repository-Specific Guidelines

This section contains guidelines specific to the contribution-guidelines repository.

### Purpose of This Repository

This repository serves as the central source of truth for contribution guidelines across all PitchConnect repositories. It contains:

1. The consolidated CONTRIBUTING.md file (this file)
2. Templates for repository-specific CONTRIBUTING.md files
3. Issue and PR templates
4. Other contribution-related documentation

### Updating Guidelines

When updating the contribution guidelines:

1. Make changes to the consolidated CONTRIBUTING.md file
2. Update any related templates or documentation
3. Create a PR to merge your changes
4. Once approved and merged, the changes will be propagated to other repositories

### Testing Changes

Before submitting a PR:

1. Preview the markdown to ensure proper formatting
2. Check that all links work correctly
3. Verify that the content is clear and consistent

### Special Considerations

Since these guidelines are used across multiple repositories:

1. Keep the language repository-agnostic where possible
2. Use clear section markers for the common content
3. Provide flexibility for repository-specific customizations
## Repository-Specific Guidelines

### API Client Specific Guidelines

This repository contains the Python client for the FOGIS API. Please follow these additional guidelines:

1. **API Versioning**: When making changes to API endpoints, ensure backward compatibility or increment the version number.
2. **Error Handling**: All API calls should have proper error handling and meaningful error messages.
3. **Documentation**: All API methods must be documented with examples.
4. **Testing**: All API methods must have both unit tests and integration tests.

<!-- END COMMON SECTION -->
