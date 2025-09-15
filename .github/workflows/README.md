# GitHub Workflow Automation

This directory contains the comprehensive GitHub Actions workflows for the FOGIS API Client project, implementing a fully automated CI/CD pipeline with branch synchronization, automated releases, and hotfix management.

## 🚀 Automated Workflow System Overview

### **Core Automation Features**
- ✅ **Automated Branch Synchronization**: Bidirectional sync between main↔develop
- ✅ **Automated Releases**: Semantic versioning with conventional commits
- ✅ **Hotfix Pipeline**: Emergency release workflow for critical fixes
- ✅ **PyPI Publishing**: Automated package publishing to PyPI
- ✅ **Container Publishing**: Automated Docker builds to GHCR
- ✅ **Quality Gates**: Comprehensive testing and validation

## 📋 Core Workflow Catalog

### **🔄 Branch Management & Releases**

#### `automated-release.yml` - **Automated Release Pipeline**
**Triggers**: Push to main, PR merge to main, manual dispatch
**Purpose**: Fully automated semantic versioning and release creation
- 🔍 **Change Detection**: Analyzes commits using conventional commit format
- 📈 **Version Calculation**: Automatic semantic version bumping (major/minor/patch)
- 🏷️ **Tag Creation**: Creates and pushes version tags
- 📝 **Release Notes**: Auto-generated categorized changelog
- 🚀 **Publishing**: Triggers PyPI and GHCR publishing workflows

#### `auto-pr-develop-to-main.yml` - **Automated PR Creation**
**Triggers**: Push to develop, workflow completion, manual dispatch
**Purpose**: Creates PRs from develop to main when tests pass
- ✅ **Test Validation**: Waits for all required workflows to pass
- 📋 **PR Creation**: Auto-creates develop→main PRs with detailed information
- 🔄 **PR Updates**: Updates existing PRs with new commits
- 🏷️ **Labeling**: Applies appropriate labels for tracking

#### `sync-main-to-develop.yml` - **Branch Synchronization**
**Triggers**: Push to main, PR merge, release completion, manual dispatch
**Purpose**: Keeps main and develop branches synchronized
- 🔄 **Bidirectional Sync**: Handles both main→develop and develop→main
- ⚠️ **Conflict Detection**: Identifies and handles merge conflicts
- 🔧 **Force Sync**: Option for manual conflict resolution
- 📊 **Sync Reporting**: Detailed sync status and commit tracking

#### `hotfix-release.yml` - **Emergency Hotfix Pipeline**
**Triggers**: Manual dispatch only
**Purpose**: Fast-track critical fixes to production
- 🚨 **Severity Levels**: Critical, high, medium severity classification
- ⚡ **Fast Track**: Optional test skipping for critical security fixes
- 🔍 **Validation**: Hotfix branch validation and testing
- 📋 **Auto PR**: Creates hotfix→main PRs with appropriate urgency
- ✅ **Auto Approval**: Auto-approves critical hotfixes

### **📦 Publishing & Distribution**

#### `publish-to-pypi.yml` - **PyPI & Container Publishing**
**Triggers**: Release creation, manual dispatch
**Purpose**: Publishes packages to PyPI and containers to GHCR
- 📦 **PyPI Publishing**: Automated package building and publishing
- 🐳 **Container Building**: Multi-platform Docker builds
- 🔍 **Version Detection**: Smart version change detection
- 🏷️ **Tagging**: Semantic version tagging for containers

#### `docker-build.yml` - **Container Build & Test**
**Triggers**: Push, PR, release, manual dispatch
**Purpose**: Builds and tests Docker containers
- 🧪 **Unit Tests**: Containerized unit test execution
- 🔗 **Integration Tests**: Full integration test suite
- 🏗️ **Production Builds**: Multi-platform production container builds
- 📊 **Caching**: Optimized build caching for faster builds

### **🧪 Testing & Quality**

#### `test.yml` - **Core Testing Pipeline**
**Triggers**: Push, PR, release
**Purpose**: Comprehensive testing and quality validation
- 🐍 **Python Testing**: pytest with coverage reporting
- 🔍 **Linting**: flake8 code quality checks
- 📊 **Coverage**: Codecov integration for coverage tracking
- 🔗 **Integration**: Docker-based integration testing

### **🔧 Maintenance & Automation**

## 🚀 Workflow Usage Guide

### **Standard Development Flow**

1. **Feature Development**
   ```bash
   # Create feature branch from develop
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-new-feature

   # Develop and commit using conventional commits
   git commit -m "feat: add new convenience method for match statistics"
   git push origin feature/my-new-feature
   ```

2. **Pull Request to Develop**
   - Create PR: `feature/my-new-feature` → `develop`
   - Tests run automatically via `test.yml` and `docker-build.yml`
   - Merge after review and tests pass

3. **Automatic Promotion to Main**
   - `auto-pr-develop-to-main.yml` creates PR: `develop` → `main`
   - Review and merge the auto-created PR

4. **Automatic Release**
   - `automated-release.yml` detects changes and creates release
   - `publish-to-pypi.yml` publishes to PyPI and GHCR
   - `sync-main-to-develop.yml` syncs main back to develop

### **Hotfix Flow**

1. **Create Hotfix Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-security-fix
   # Make critical fixes
   git commit -m "fix!: resolve critical security vulnerability"
   git push origin hotfix/critical-security-fix
   ```

2. **Deploy Hotfix**
   - Go to Actions → "Hotfix Release Pipeline"
   - Run workflow with hotfix branch name and severity
   - Review auto-created PR and merge
   - Release deploys automatically

### **Manual Release**

```bash
# Trigger manual release
gh workflow run automated-release.yml \
  --field release_type=minor \
  --field skip_tests=false
```

### **Emergency Procedures**

#### Force Sync Branches
```bash
gh workflow run sync-main-to-develop.yml \
  --field sync_direction=bidirectional \
  --field force_sync=true
```

#### Emergency PyPI Publish
```bash
gh workflow run publish-to-pypi.yml \
  --field version_type=patch \
  --field force_publish=true
```

## 📊 Workflow Monitoring

### **Key Metrics Tracked**
- ✅ **Test Success Rate**: All workflows report test results
- 📈 **Release Frequency**: Automated release tracking
- 🔄 **Sync Success**: Branch synchronization monitoring
- 📦 **Deployment Success**: PyPI and GHCR publish tracking

### **Troubleshooting Common Issues**

#### Branch Sync Conflicts
- Check `sync-main-to-develop.yml` logs
- Use manual force sync if needed
- Review conflict resolution in created issues

#### Failed Releases
- Check `automated-release.yml` for version detection issues
- Verify conventional commit format
- Check PyPI token validity

#### Test Failures
- Review `test.yml` and `docker-build.yml` logs
- Check for dependency issues
- Verify Docker environment setup

## Issue and PR Automation

The following workflows automate the management of issues and pull requests:

### Issue Labeler

**File:** `issue-labeler.yml`

**Triggers:** When an issue is opened

**Actions:**
- Adds the `triage` label to new issues
- Adds the `ready-for-development` label to non-draft issues

### PR Status Tracker

**File:** `pr-status-tracker.yml`

**Triggers:** When a PR is opened, converted to draft, marked ready for review, or closed

**Actions:**
- For draft PRs:
  - Extracts issue references from the PR description
  - Removes the `ready-for-development` label from referenced issues
  - Adds the `in-progress` label to referenced issues
  - Adds a comment to referenced issues

- For PRs marked ready for review:
  - Extracts issue references from the PR description
  - Removes the `in-progress` label from referenced issues
  - Adds the `review-ready` label to referenced issues
  - Adds a comment to referenced issues

- For merged PRs:
  - Extracts issue references from the PR description
  - Removes the `review-ready` label from referenced issues
  - Adds the `merged-to-develop` label to referenced issues
  - Adds a comment to referenced issues

### PR Tracker

**File:** `pr-tracker.yml`

**Triggers:** When a PR is opened, reopened, converted to draft, marked ready for review, or closed

**Actions:**
- Adds the PR to the organization PR tracker project board
- Updates the PR status in the project board based on the PR event

### Issue Updater

**File:** `issue-updater.yml`

**Triggers:** When a PR is closed (merged or not merged)

**Actions:**
- For merged PRs:
  - Extracts issue references from the PR description
  - Removes the `review-ready` and `in-progress` labels from referenced issues
  - Adds the `merged-to-develop` label (or `released` if merged to main) to referenced issues
  - Adds the `done` label to referenced issues
  - Closes the referenced issues
  - Adds a comment to referenced issues

- For closed but not merged PRs:
  - Extracts issue references from the PR description
  - Removes the `in-progress` and `review-ready` labels from referenced issues
  - Adds the `ready-for-development` label to referenced issues
  - Adds a comment to referenced issues

## Label Management

### Label Creator

**File:** `label-creator.yml`

**Triggers:** Manual workflow dispatch

**Actions:**
- Creates standard labels in the repository if they don't already exist

## Required Labels

The following labels are used by the workflows:

- `triage`: Needs triage by maintainers
- `ready-for-development`: Triaged and ready for someone to work on
- `in-progress`: Issue is being worked on in a draft PR
- `review-ready`: Work is complete and ready for review
- `merged-to-develop`: Implementation has been merged to develop
- `released`: Feature has been released to production
- `done`: Issue has been completed and closed

## Usage

### Setting Up a New Repository

1. Ensure the repository has the necessary workflows in the `.github/workflows` directory
2. Run the Label Creator workflow to create the required labels:
   - Go to the "Actions" tab
   - Select the "Label Creator" workflow
   - Click "Run workflow"
   - Click "Run workflow" again to confirm

### Creating Issues

1. Create a new issue with a clear title and description
2. The Issue Labeler workflow will automatically add the `triage` and `ready-for-development` labels

### Working on Issues

1. Create a draft PR that references the issue (e.g., "Fixes #123")
2. The PR Status Tracker workflow will automatically update the issue with the `in-progress` label
3. When the PR is ready for review, mark it as "Ready for review"
4. The PR Status Tracker workflow will automatically update the issue with the `review-ready` label
5. When the PR is merged, the Issue Updater workflow will automatically close the issue and add the `done` label

## Troubleshooting

If the workflows are not working as expected, check the following:

1. Ensure the repository has the required labels (run the Label Creator workflow)
2. Check the workflow run logs for any errors
3. Verify that the PR description correctly references the issue (e.g., "Fixes #123")
4. Ensure the workflows have the necessary permissions (issues: write, pull-requests: write, contents: read)
