# Branch Synchronization Strategy

## 🎯 **Overview**

This document outlines the comprehensive branch synchronization strategy for the FOGIS API Client repository, maintaining consistency between `main` and `develop` branches while allowing flexibility for different types of changes.

## 🔄 **Synchronization Workflows**

### **1. Standard Flow: develop → main**
- **Trigger**: Automatic when tests pass on develop
- **Workflow**: `auto-pr-develop-to-main.yml`
- **Purpose**: Regular feature integration and releases

### **2. Reverse Flow: main → develop**
- **Trigger**: Automatic when commits are pushed to main
- **Workflow**: `sync-main-to-develop.yml`
- **Purpose**: Keep develop updated with hotfixes and infrastructure changes

## 📋 **Workflow Details**

### **Auto PR Develop to Main (`auto-pr-develop-to-main.yml`)**

**Triggers:**
- Push to develop branch
- Successful completion of Tests and Code Quality workflows
- Manual dispatch for testing

**Process:**
1. ✅ Verify all required tests pass
2. ✅ Check for existing develop→main PRs
3. ✅ Create new PR or update existing one
4. ✅ Add appropriate labels and notifications

**Enhanced Features:**
- Detects recent sync activity to avoid conflicts
- Provides detailed commit summaries
- Handles existing PR updates gracefully
- Integrates with PyPI publishing workflow

### **Sync Main to Develop (`sync-main-to-develop.yml`)**

**Triggers:**
- Push to main branch
- PR merged to main
- Manual dispatch with force sync option

**Process:**
1. ✅ Check if develop branch exists (create if missing)
2. ✅ Detect merge conflicts before attempting sync
3. ✅ Perform clean merge or handle conflicts
4. ✅ Update existing auto-PRs with sync information
5. ✅ Create notification issues for manual resolution

**Conflict Resolution:**
- **Clean merge**: Automatic synchronization
- **Conflicts detected**: Create issue for manual resolution
- **Force sync**: Manual override option available

## 🚨 **Conflict Handling**

### **Automatic Detection**
The sync workflow uses `git merge-tree` to detect conflicts before attempting merge:
```bash
git merge-tree $(git merge-base origin/main origin/develop) origin/main origin/develop
```

### **Resolution Options**

#### **Option 1: Manual Resolution (Recommended)**
```bash
git checkout develop
git pull origin develop
git merge main
# Resolve conflicts in your editor
git add .
git commit -m "Resolve merge conflicts from main sync"
git push origin develop
```

#### **Option 2: Force Sync (Use with caution)**
- Trigger the sync workflow manually
- Enable "force_sync" option
- Uses `--strategy-option=theirs` to prefer main changes

#### **Option 3: Reset Develop to Main**
```bash
git checkout develop
git reset --hard main
git push --force origin develop
```

#### **Option 4: Use Sync Script**
```bash
# Check for conflicts first
./scripts/sync-branches.sh --dry-run main develop

# Perform sync if no conflicts
./scripts/sync-branches.sh main develop

# Force sync if needed (use with caution)
./scripts/sync-branches.sh --force main develop
```

## 📊 **Monitoring and Notifications**

### **Successful Synchronization**
- ✅ Automatic comments on existing auto-PRs
- ✅ Summary of synced commits
- ✅ Merge type indication (clean vs. force)

### **Conflict Detection**
- 🚨 Automatic issue creation
- 📋 List of conflicting files
- 📝 Resolution instructions
- 🏷️ Appropriate labels for tracking

### **PR Management**
- 🔄 Automatic PR creation when tests pass
- 📈 Commit count and change summaries
- 🏷️ Labels: `automated-pr`, `develop-to-main`, `ready-for-review`
- 📝 Detailed PR descriptions with checklists

## 🛠️ **Manual Tools**

### **Branch Sync Script (`scripts/sync-branches.sh`)**

**Features:**
- Dry-run mode for safe testing
- Force sync option for conflict override
- Verbose output for detailed information
- Conflict detection and reporting
- Colored output for better readability

**Usage Examples:**
```bash
# Check sync status (dry run)
./scripts/sync-branches.sh --dry-run main develop

# Sync with verbose output
./scripts/sync-branches.sh --verbose main develop

# Force sync despite conflicts
./scripts/sync-branches.sh --force main develop

# Check reverse sync status
./scripts/sync-branches.sh --dry-run develop main
```

**Options:**
- `-d, --dry-run`: Show what would be done without making changes
- `-f, --force`: Force synchronization even if conflicts exist
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

## 🔧 **Configuration**

### **Required Workflows**
The auto-PR workflow requires these workflows to pass:
- `Tests`: Unit and integration tests
- `Code Quality`: Linting, formatting, and security checks

### **Labels Used**
- `automated-pr`: Marks PRs created by automation
- `develop-to-main`: Indicates direction of PR
- `ready-for-review`: PR is ready for human review
- `sync-conflict`: Indicates synchronization conflicts
- `needs-attention`: Requires manual intervention
- `manual-resolution-required`: Conflicts need manual resolution

### **Branch Protection**
Ensure branch protection rules are configured:
- Require PR reviews for main branch
- Require status checks to pass
- Require branches to be up to date before merging

## 📈 **Best Practices**

### **For Developers**
1. **Regular Sync**: Keep develop branch updated with main
2. **Small PRs**: Create focused, reviewable pull requests
3. **Test Locally**: Run tests before pushing to develop
4. **Resolve Conflicts**: Address sync conflicts promptly

### **For Maintainers**
1. **Monitor Workflows**: Check for failed sync attempts
2. **Review Auto-PRs**: Validate automated pull requests
3. **Handle Conflicts**: Resolve sync conflicts quickly
4. **Update Documentation**: Keep sync strategy current

### **For Releases**
1. **Stable Main**: Keep main branch always deployable
2. **Feature Branches**: Use develop for feature integration
3. **Hotfix Process**: Apply critical fixes to main first
4. **Version Tags**: Tag releases on main branch

## 🚀 **Workflow Integration**

### **CI/CD Pipeline**
The synchronization strategy integrates with:
- **Testing**: Automated test execution on develop
- **Quality Checks**: Code quality validation
- **Publishing**: PyPI package publishing from main
- **Deployment**: Automatic deployment workflows

### **Release Process**
1. Features developed on feature branches
2. Feature branches merged to develop
3. Tests pass on develop → Auto-PR created
4. PR reviewed and merged to main
5. Main branch triggers publishing/deployment

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Sync Conflicts**
- **Symptom**: Automatic sync fails with conflicts
- **Solution**: Use manual resolution or sync script
- **Prevention**: Regular syncing, smaller changes

#### **Failed Auto-PRs**
- **Symptom**: No PR created despite passing tests
- **Solution**: Check workflow logs, verify test results
- **Prevention**: Ensure all required workflows are configured

#### **Stale Branches**
- **Symptom**: Develop branch falls behind main
- **Solution**: Manual sync or force sync
- **Prevention**: Regular monitoring, automated sync

### **Debug Commands**
```bash
# Check branch status
git log --oneline --graph main develop

# Check for conflicts
./scripts/sync-branches.sh --dry-run main develop

# View workflow logs
gh run list --workflow=sync-main-to-develop.yml

# Check PR status
gh pr list --head develop --base main
```

## 📚 **Additional Resources**

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Git Merge Strategies](https://git-scm.com/docs/merge-strategies)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)

---

**This synchronization strategy ensures consistent, reliable branch management while maintaining development velocity and code quality for the FOGIS API Client repository.**
