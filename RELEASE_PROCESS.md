# Release Process Documentation

This document outlines the complete workflow for releasing new versions of the fogis-api-client-python package, from merging fixes to having them available as published releases.

## Overview

The repository uses a **GitFlow-based workflow** with automated release processes:

- **`develop`** - Integration branch for new features and fixes
- **`main`** - Production-ready code, triggers releases
- **Feature/Bugfix branches** - Individual changes (like our issue #249 fix)

## Step-by-Step Release Process

### 1. Development and PR Workflow

1. **Create feature/bugfix branch** from `develop`:
   ```bash
   git checkout develop
   git pull
   git checkout -b bugfix/issue-249-match-list-filter-parameter-fix
   ```

2. **Implement changes and create PR** to `develop`:
   - ✅ **COMPLETED**: PR #250 created and ready for review
   - Include "Fixes #XXX" in PR description for automatic issue linking
   - Ensure all tests pass and code follows project standards

3. **Review and merge PR** to `develop`:
   - Maintainers review the PR
   - All CI/CD checks must pass
   - PR gets merged to `develop` branch

### 2. Automated Develop → Main Workflow

Once changes are merged to `develop`, the automated workflow kicks in:

#### Auto-PR Creation (`auto-pr-develop-to-main.yml`)

**Triggers:**
- Push to `develop` branch
- Successful completion of Tests and Code Quality workflows

**Process:**
1. **Waits for all tests to pass** on `develop` branch
2. **Checks for differences** between `develop` and `main`
3. **Creates automatic PR** from `develop` to `main` if:
   - All required workflows (Tests, Code Quality) pass ✅
   - There are changes between branches
   - No existing develop→main PR exists

**PR Details:**
- Title: `🚀 Auto-merge: Develop to Main (X commits)`
- Includes recent commits and workflow status
- Automatically labeled: `automated-pr`, `develop-to-main`, `ready-for-review`

### 3. Main Branch Merge and Release

#### Manual Review and Merge
1. **Review the auto-generated PR** from develop→main
2. **Verify all changes** are ready for production
3. **Merge the PR** to `main` branch

#### Automated Publishing (`publish-to-pypi.yml`)

**Triggers automatically when:**
- Code is pushed to `main` branch
- Version in `setup.py` differs from PyPI
- Manual workflow dispatch
- GitHub release is created

**Publishing Process:**

1. **Version Check:**
   - Compares current version in `setup.py` with PyPI
   - Current version: `0.5.4` (from setup.py line 9)
   - Only publishes if version has changed

2. **PyPI Publishing:**
   - Builds Python package using `python -m build`
   - Validates package with `twine check`
   - Publishes to PyPI using `pypa/gh-action-pypi-publish`
   - Requires `PYPI_API_TOKEN` secret

3. **Container Publishing (GHCR):**
   - Builds multi-platform Docker images (linux/amd64, linux/arm64)
   - Publishes to GitHub Container Registry
   - Tags: `latest`, version-specific, semantic versioning

### 4. Manual Release Options

#### Option A: Manual Version Bump and Release

```bash
# Trigger manual release workflow
gh workflow run publish-to-pypi.yml \
  --field version_type=patch \  # or minor, major
  --field dry_run=false
```

**Process:**
1. Automatically bumps version using `bump2version`
2. Builds and publishes to PyPI
3. Creates GitHub release with auto-generated notes
4. Publishes container to GHCR

#### Option B: GitHub Release Creation

1. **Create GitHub release** manually:
   - Go to GitHub → Releases → "Create a new release"
   - Tag: `v0.5.5` (next version)
   - Title: `Release v0.5.5`
   - Auto-generate release notes or write custom notes

2. **Automatic publishing** triggers on release creation

## Version Numbering Convention

**Current Version:** `0.5.4`

**Semantic Versioning (SemVer):**
- **MAJOR** (0.x.x): Breaking changes
- **MINOR** (x.5.x): New features, backward compatible
- **PATCH** (x.x.4): Bug fixes, backward compatible

**For Issue #249 Fix:**
- Recommended: **PATCH** version bump → `0.5.5`
- Reason: Bug fix, no breaking changes, backward compatible

## Release Artifacts

### PyPI Package
- **Package Name:** `fogis-api-client-timmyBird`
- **Installation:** `pip install fogis-api-client-timmyBird==0.5.5`
- **URL:** https://pypi.org/project/fogis-api-client-timmyBird/

### GitHub Container Registry (GHCR)
- **Registry:** `ghcr.io/pitchconnect/fogis-api-client-python`
- **Tags:** `latest`, `0.5.5`, `0.5`, `0`
- **Usage:** `docker pull ghcr.io/pitchconnect/fogis-api-client-python:0.5.5`

## Required Secrets and Permissions

### Repository Secrets
- `PYPI_API_TOKEN` - PyPI publishing token
- `GITHUB_TOKEN` - Automatic (for GHCR publishing)

### Permissions Required
- **Maintainer access** to merge PRs to `main`
- **Release permissions** for manual releases
- **Workflow dispatch** permissions for manual triggers

## Changelog Management

### Location
- **File:** `changelog.md`
- **Format:** Keep-a-Changelog format

### Update Process
1. **Add entry** for new version before release
2. **Include:** Added, Changed, Fixed, Removed sections
3. **Example entry for Issue #249:**

```markdown
## [0.5.5] - 2025-08-04

### Fixed
- Fixed TypeError in MatchListFilter.fetch_filtered_matches() (fixes #249)
- Corrected parameter name from 'filter' to 'filter_params' in API call
- Added robust response handling and fallback mechanisms
- Improved error handling and documentation
```

## Next Steps for Issue #249

1. **✅ COMPLETED:** PR #250 created and ready for review
2. **PENDING:** Maintainer review and merge of PR #250 to `develop`
3. **AUTOMATIC:** Auto-PR creation from `develop` to `main`
4. **MANUAL:** Review and merge auto-PR to `main`
5. **MANUAL:** Update version in `setup.py` from `0.5.4` to `0.5.5`
6. **AUTOMATIC:** PyPI and GHCR publishing triggered by `main` branch push

## Monitoring Release Status

### Check CI/CD Status
```bash
# Check workflow status
gh run list --workflow=publish-to-pypi.yml

# Check specific run
gh run view <run-id>
```

### Verify Release
- **PyPI:** https://pypi.org/project/fogis-api-client-timmyBird/
- **GHCR:** https://github.com/PitchConnect/fogis-api-client-python/pkgs/container/fogis-api-client-python
- **GitHub Releases:** https://github.com/PitchConnect/fogis-api-client-python/releases

## Troubleshooting

### Common Issues
1. **Version not bumped:** Update `setup.py` version manually
2. **Tests failing:** Fix issues before merge to `main`
3. **PyPI token expired:** Update `PYPI_API_TOKEN` secret
4. **Container build fails:** Check Dockerfile and dependencies

### Emergency Hotfix Process
1. Create hotfix branch from `main`
2. Implement fix and test
3. Create PR directly to `main` (bypass develop)
4. Merge and release immediately
