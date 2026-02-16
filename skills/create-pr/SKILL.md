---
name: create-pr
description: Create GitHub pull requests using gh CLI. Use when the user asks to open, create, or submit pull requests.
argument-hint: "[--draft]"
---

# Create Pull Request

Create a GitHub pull request for the current branch using `gh pr create`.

## Arguments

- No argument: create a regular PR
- `--draft`: create as a draft PR

## Workflow

### 1. Context Gathering

Run these commands to understand the current state:

Current branch:
```bash
git branch --show-current
```

Determine the default base branch:
```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo main
```

Working tree state:
```bash
git status
```

**Note**: Never use the `-uall` flag with git status.

Commits on this branch (vs base):
```bash
git log --oneline $(git merge-base HEAD <base-branch>)..HEAD
```

Changed files summary:
```bash
git diff $(git merge-base HEAD <base-branch>)..HEAD --stat
```

Full diff for analysis:
```bash
git diff $(git merge-base HEAD <base-branch>)..HEAD
```

Check for an existing open PR on this branch:
```bash
gh pr list --head $(git branch --show-current) --state open
```

Check if the branch is pushed to remote:
```bash
git ls-remote --heads origin <current-branch>
```

### 2. Safety Checks

Abort or warn in these scenarios:

- **On main/master branch**: STOP. Inform the user that PRs cannot be created from the default branch.
- **Detached HEAD state**: STOP. If `git branch --show-current` returns empty, inform the user they are in detached HEAD state and must checkout a branch first.
- **No commits vs base**: STOP. If `git log` shows no commits between the branch and base, inform the user there is nothing to create a PR for.
- **Existing open PR for this branch**: WARN. Show the existing PR link and ask the user if they want to continue or update the existing PR instead.
- **Uncommitted changes**: WARN. Inform the user about uncommitted changes and suggest committing first before creating the PR.
- **Secrets in diff**: Check the diff for files like `.env`, `credentials.json`, `*.pem`, `*.key`, or lines containing API keys and tokens. WARN the user and do not include sensitive content in the PR title or body.
- **Branch not pushed to remote**: Push the branch before creating the PR:

```bash
git push -u origin <current-branch>
```

### 3. Analyze Changes

Look at ALL commits and the full diff from Context Gathering:

- Summarize what changed functionally
- Determine the primary change type:
  - New feature → `feat`
  - Bug fix → `fix`
  - Code restructuring → `refactor`
  - Maintenance, dependencies, tooling → `chore`
  - Documentation → `docs`
  - Tests → `test`
  - Formatting → `style`
  - Performance → `perf`
  - CI/CD → `ci`
  - Build system → `build`

When changes span multiple types, use the type of the primary change.

### 4. Check for PR Template

Look for a PR template file in the repository:

```bash
fd -iH "pull_request_template" --type f 2>/dev/null || echo "No template found"
```

If a template is found, read it and use its structure for the PR body. If no template is found, use this default structure:

```
## Summary

- <bullet points describing what changed>

## Type of Change

- [x] <type>: <description>

## Test Plan

- <verification steps>
```

### 5. Draft PR Title and Body

Follow these conventions:

**Title**:
- Format: `type: description`
- Imperative mood (e.g., "Add feature" not "Added feature")
- ≤ 70 characters
- Factual language — describe what the code does now

**Body**:
- Fill in all PR template sections based on the actual changes
- Summary section: 1-3 bullet points covering the changes
- Type of Change section: check the one that applies
- Test Plan section: actionable verification steps
- Banned words in title and body: critical, crucial, essential, significant, comprehensive, robust, elegant

### 6. Create PR

Use HEREDOC format for the PR body:

```bash
gh pr create --title "type: PR title" --body "$(cat <<'EOF'
PR body here following template
EOF
)"
```

Add the `--draft` flag if the user requested a draft PR.

### 7. Verify

After creating the PR, confirm it was created:

```bash
gh pr view --web 2>/dev/null || gh pr view
```

Return the PR URL to the user.

## Edge Cases

Handle these scenarios gracefully:

- **No remote configured**: If `git remote` returns empty, inform the user they need to add a remote first. Stop.
- **Merge conflicts with base**: If `git merge-base` fails or the diff shows conflicts, warn the user to rebase or merge the base branch before creating the PR.
- **gh CLI not authenticated**: If `gh pr create` fails with an authentication error, inform the user to run `gh auth login` first. Stop.

## Important Rules

- **NEVER** force push
- **NEVER** create PRs targeting main from main
- **NEVER** skip the PR template if one exists in the repository
- **ALWAYS** push the branch before creating the PR
- **ALWAYS** use HEREDOC format for the PR body
- **ALWAYS** return the PR URL when done
- **DO NOT** include secrets or credentials in the PR title or body
