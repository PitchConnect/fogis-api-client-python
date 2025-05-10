# GitHub Workflow Automation

This directory contains GitHub Actions workflows that automate various tasks in the repository.

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
