---
name: commit
description: Create git commits following project conventions. Use when the user asks to commit changes, save work, or create commits.
argument-hint: "[--all | --staged]"
---

# Commit Changes

Create a git commit with staged or all changes, following project commit conventions.

## Arguments

- No argument or `--staged`: commit only staged files (default)
- `--all` or `-a`: stage and commit ALL files (tracked modified + untracked)

## Workflow

### 1. Context Gathering

Run these commands to understand the current state:

```bash
git status
```

```bash
git diff --cached
```

```bash
git diff
```

```bash
git log --oneline -5
```

**Note**: Never use the `-uall` flag with git status.

### 2. Safety Checks

Abort or warn in these scenarios:

- **On main/master branch**: WARN the user and ask for confirmation before proceeding
- **Nothing staged (default mode) and no changes**: Inform user and stop
- **Nothing staged (default mode) but unstaged changes exist**: Inform user they have unstaged changes and suggest using `--all` or staging manually
- **Secrets files detected**: Check for files like `.env`, `credentials.json`, `*.pem`, `*.key`, etc. — warn and exclude them from staging
- **Detached HEAD state**: Inform user and stop

### 3. Staging (--all mode only)

When using `--all` or `-a`:

1. List all modified and untracked files from git status
2. Add files by specific name (NOT `git add -A` or `git add .`)
3. Exclude secrets files from staging

### 4. Analyze Changes

Look at all staged changes:

```bash
git diff --cached
```

Summarize the nature of changes and determine the commit type:
- New feature → `feat`
- Enhancement to existing feature → `feat` (new capability) or `refactor` (restructuring)
- Bug fix → `fix`
- Refactoring → `refactor`
- Tests → `test`
- Documentation → `docs`
- Chores → `chore`
- Styling → `style`
- Performance → `perf`
- CI changes → `ci`
- Build changes → `build`

When changes span multiple types (e.g., a feature and its tests), use the type of the primary change. The most impactful change determines the type.

Ensure the message accurately reflects changes and their purpose.

### 5. Draft Commit Message

Follow these conventions:
- Format: `type: subject line`
- Imperative mood (e.g., "Add feature" not "Added feature")
- ≤ 72-character subject line (including the `type: ` prefix)
- Focus on "why" rather than "what"
- 1-2 sentences maximum
- Match the style of recent commits in the repository

Examples:
- `feat: Add user authentication endpoint`
- `fix: Correct off-by-one error in pagination`
- `refactor: Extract validation logic into shared module`
- `docs: Add API usage examples to README`
- `chore: Update dependency versions`
- `test: Add edge case coverage for user input`
- `style: Apply consistent formatting to auth module`
- `perf: Optimize database query for user lookup`
- `ci: Add automated security scanning workflow`
- `build: Update webpack configuration for production`

### 6. Create Commit

Use HEREDOC format to ensure proper message formatting:

```bash
git commit -m "$(cat <<'EOF'
type: Commit message here
EOF
)"
```

### 7. Verify

After the commit completes, verify success:

```bash
git status
```

### 8. Pre-commit Hook Failure

If the commit fails due to a pre-commit hook:

1. Fix the issue identified by the hook
2. Re-stage the affected files
3. Create a NEW commit (NEVER amend)

**Warning**: Amending after hook failure would modify the previous commit, potentially destroying work. Always create a new commit instead.

## Important Rules

- **NEVER** use `git add -A` or `git add .` — always add files by specific name
- **NEVER** amend commits — always create new commits
- **NEVER** push unless explicitly asked by the user
- **NEVER** skip hooks (no `--no-verify` flag)
- **ALWAYS** use HEREDOC format for commit messages
- **DO NOT** commit files that likely contain secrets
- If there are no changes to commit, do not create an empty commit
