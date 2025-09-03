#!/bin/bash

# Branch Synchronization Script for FOGIS API Client
# This script provides comprehensive branch synchronization capabilities
# between main and develop branches with conflict detection and resolution.

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/sync-branches.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis for better visual feedback
SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"
SYNC="🔄"
CONFLICT="🚨"
FORCE="⚡"

# Default values
DRY_RUN=false
FORCE_SYNC=false
SOURCE_BRANCH=""
TARGET_BRANCH=""
VERBOSE=false

# Function to print colored output
print_status() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "SUCCESS")
            echo -e "${GREEN}${SUCCESS} ${message}${NC}"
            ;;
        "ERROR")
            echo -e "${RED}${ERROR} ${message}${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}${WARNING} ${message}${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}${INFO} ${message}${NC}"
            ;;
        "SYNC")
            echo -e "${CYAN}${SYNC} ${message}${NC}"
            ;;
        "CONFLICT")
            echo -e "${PURPLE}${CONFLICT} ${message}${NC}"
            ;;
        "FORCE")
            echo -e "${YELLOW}${FORCE} ${message}${NC}"
            ;;
    esac
    
    # Log to file if logs directory exists
    if [[ -d "$PROJECT_ROOT/logs" ]]; then
        echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
Branch Synchronization Script for FOGIS API Client

USAGE:
    $0 [OPTIONS] <source-branch> <target-branch>

ARGUMENTS:
    source-branch    Source branch to sync from (e.g., main)
    target-branch    Target branch to sync to (e.g., develop)

OPTIONS:
    -d, --dry-run       Show what would be done without making changes
    -f, --force         Force synchronization even if conflicts exist
    -v, --verbose       Enable verbose output
    -h, --help          Show this help message

EXAMPLES:
    # Sync main to develop (dry run)
    $0 --dry-run main develop

    # Force sync main to develop
    $0 --force main develop

    # Check develop to main sync status
    $0 --dry-run develop main

    # Verbose sync with conflict detection
    $0 --verbose main develop

COMMON WORKFLOWS:
    # Standard main → develop sync
    $0 main develop

    # Check for conflicts before syncing
    $0 --dry-run main develop

    # Force sync when conflicts exist (use with caution)
    $0 --force main develop

EOF
}

# Function to validate git repository
validate_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_status "ERROR" "Not in a git repository"
        exit 1
    fi
    
    # Ensure we're in the project root
    cd "$PROJECT_ROOT"
    print_status "INFO" "Working in repository: $(pwd)"
}

# Function to fetch latest changes
fetch_branches() {
    print_status "SYNC" "Fetching latest changes from remote..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "INFO" "[DRY RUN] Would fetch all branches from origin"
        return 0
    fi
    
    git fetch origin --prune
    print_status "SUCCESS" "Fetched latest changes"
    
    if [[ "$VERBOSE" == "true" ]]; then
        print_status "INFO" "Available remote branches:"
        git branch -r | head -10
    fi
}

# Function to check if branch exists
check_branch_exists() {
    local branch=$1
    local branch_type=$2
    
    if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
        print_status "SUCCESS" "$branch_type branch '$branch' exists"
        return 0
    else
        print_status "ERROR" "$branch_type branch '$branch' does not exist"
        return 1
    fi
}

# Function to get branch status
get_branch_status() {
    local source=$1
    local target=$2
    
    print_status "INFO" "Checking branch status..."
    
    # Get commit SHAs
    local source_sha=$(git rev-parse "origin/$source")
    local target_sha=$(git rev-parse "origin/$target")
    
    print_status "INFO" "Source ($source): $source_sha"
    print_status "INFO" "Target ($target): $target_sha"
    
    # Check if branches are in sync
    if [[ "$source_sha" == "$target_sha" ]]; then
        print_status "SUCCESS" "Branches are already in sync"
        return 0
    else
        print_status "SYNC" "Branches need synchronization"
        
        # Show commit differences
        local ahead_count=$(git rev-list --count "origin/$target..origin/$source")
        local behind_count=$(git rev-list --count "origin/$source..origin/$target")
        
        print_status "INFO" "$target is $ahead_count commits behind $source"
        print_status "INFO" "$target is $behind_count commits ahead of $source"
        
        if [[ "$VERBOSE" == "true" && "$ahead_count" -gt 0 ]]; then
            print_status "INFO" "Commits to be synced:"
            git log --oneline "origin/$target..origin/$source" --pretty=format:"  - %s (%h)" | head -5
            if [[ "$ahead_count" -gt 5 ]]; then
                print_status "INFO" "  ... and $((ahead_count - 5)) more commits"
            fi
        fi
        
        return 1
    fi
}

# Function to check for merge conflicts
check_conflicts() {
    local source=$1
    local target=$2
    
    print_status "INFO" "Checking for potential merge conflicts..."
    
    # Use git merge-tree to detect conflicts without actually merging
    local merge_base=$(git merge-base "origin/$source" "origin/$target")
    local merge_tree_output=$(git merge-tree "$merge_base" "origin/$source" "origin/$target")
    
    if echo "$merge_tree_output" | grep -q "<<<<<<< "; then
        print_status "CONFLICT" "Merge conflicts detected"
        
        # Extract conflicting files
        local conflicting_files=$(echo "$merge_tree_output" | grep "<<<<<<< " | cut -d' ' -f2 | sort -u)
        print_status "WARNING" "Conflicting files:"
        echo "$conflicting_files" | while read -r file; do
            print_status "WARNING" "  - $file"
        done
        
        return 1
    else
        print_status "SUCCESS" "No merge conflicts detected"
        return 0
    fi
}

# Function to perform the sync
perform_sync() {
    local source=$1
    local target=$2
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "INFO" "[DRY RUN] Would sync $source → $target"
        return 0
    fi
    
    print_status "SYNC" "Starting synchronization: $source → $target"
    
    # Checkout target branch
    git checkout "$target"
    git reset --hard "origin/$target"
    
    if [[ "$FORCE_SYNC" == "true" ]]; then
        print_status "FORCE" "Force merging $source into $target"
        git merge "origin/$source" --strategy-option=theirs --no-edit
        print_status "WARNING" "Force merge completed - manual review recommended"
    else
        print_status "SYNC" "Performing clean merge"
        git merge "origin/$source" --no-edit
        print_status "SUCCESS" "Clean merge completed"
    fi
    
    # Push the synchronized branch
    git push origin "$target"
    print_status "SUCCESS" "Synchronized $target branch pushed to remote"
}

# Function to show sync summary
show_sync_summary() {
    local source=$1
    local target=$2
    
    print_status "INFO" "Synchronization Summary:"
    print_status "INFO" "  Source: $source"
    print_status "INFO" "  Target: $target"
    print_status "INFO" "  Dry Run: $DRY_RUN"
    print_status "INFO" "  Force Sync: $FORCE_SYNC"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Get sync details
        local synced_commits=$(git rev-list --count "origin/$source..HEAD" 2>/dev/null || echo "0")
        print_status "SUCCESS" "Synchronization completed successfully"
        print_status "INFO" "  Commits synced: $synced_commits"
    fi
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE_SYNC=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*)
                print_status "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [[ -z "$SOURCE_BRANCH" ]]; then
                    SOURCE_BRANCH=$1
                elif [[ -z "$TARGET_BRANCH" ]]; then
                    TARGET_BRANCH=$1
                else
                    print_status "ERROR" "Too many arguments"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Validate arguments
    if [[ -z "$SOURCE_BRANCH" || -z "$TARGET_BRANCH" ]]; then
        print_status "ERROR" "Both source and target branches must be specified"
        show_usage
        exit 1
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/logs"
    
    print_status "INFO" "FOGIS API Client Branch Synchronization"
    print_status "INFO" "======================================="
    
    # Validate git repository
    validate_git_repo
    
    # Fetch latest changes
    fetch_branches
    
    # Check if branches exist
    if ! check_branch_exists "$SOURCE_BRANCH" "Source"; then
        exit 1
    fi
    
    if ! check_branch_exists "$TARGET_BRANCH" "Target"; then
        exit 1
    fi
    
    # Check branch status
    if get_branch_status "$SOURCE_BRANCH" "$TARGET_BRANCH"; then
        print_status "SUCCESS" "No synchronization needed"
        exit 0
    fi
    
    # Check for conflicts
    if ! check_conflicts "$SOURCE_BRANCH" "$TARGET_BRANCH"; then
        if [[ "$FORCE_SYNC" == "true" ]]; then
            print_status "WARNING" "Conflicts detected but force sync enabled"
        else
            print_status "ERROR" "Conflicts detected. Use --force to override or resolve manually"
            print_status "INFO" "Manual resolution steps:"
            print_status "INFO" "  1. git checkout $TARGET_BRANCH"
            print_status "INFO" "  2. git merge $SOURCE_BRANCH"
            print_status "INFO" "  3. Resolve conflicts manually"
            print_status "INFO" "  4. git commit && git push origin $TARGET_BRANCH"
            exit 1
        fi
    fi
    
    # Perform the synchronization
    perform_sync "$SOURCE_BRANCH" "$TARGET_BRANCH"
    
    # Show summary
    show_sync_summary "$SOURCE_BRANCH" "$TARGET_BRANCH"
    
    print_status "SUCCESS" "Branch synchronization completed!"
}

# Run main function with all arguments
main "$@"
