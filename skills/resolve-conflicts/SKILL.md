---
name: resolve-conflicts
description: Detect, analyze, and resolve git merge conflicts with user guidance. Use when the user asks to resolve conflicts, handle merge conflicts, or fix conflicts after a merge or rebase.
argument-hint: ""
---

# Resolve Merge Conflicts

Detect and resolve git merge conflicts in the working tree after a merge or rebase operation.

## Scope

This skill resolves conflicts in the working tree that resulted from a merge or rebase. It does NOT initiate merge or rebase operations. Use this after `git merge` or `git rebase` when conflicts occur.

## Workflow

### 1. Context Gathering

Run these commands to understand the current state:

Current branch:
```bash
git branch --show-current
```

Check for conflicts:
```bash
git status
```

List conflicted files:
```bash
git diff --name-only --diff-filter=U
```

Search for conflict markers in tracked files:
```bash
rg "^<<<<<<< " --files-with-matches
```

**Note**: Never use the `-uall` flag with git status.

### 2. Safety Checks

Abort in these scenarios:

- **Detached HEAD state**: If `git branch --show-current` returns empty, inform the user they are in detached HEAD state and cannot proceed.
- **No merge/rebase in progress**: If git status shows no merge or rebase in progress AND no conflicted files exist, check for PR-level conflicts before aborting (see below).
- **No conflicts found**: If both `git diff --diff-filter=U` and `rg` return no results, check for PR-level conflicts before aborting (see below).

**PR conflict check** — when no local conflicts exist, check if the current branch has a PR with unresolved conflicts:

```bash
gh pr view --json mergeStateStatus,baseRefName --jq '{status: .mergeStateStatus, base: .baseRefName}'
```

- If `gh` is not available or no PR exists, STOP with: "No merge conflicts detected. Working tree is clean."
- If `mergeStateStatus` is `DIRTY`, inform the user:
  > "Your PR has conflicts with `<base>`. To resolve them locally, run:
  > `git fetch origin && git merge origin/<base>` (or `git rebase origin/<base>` if your project uses rebase).
  > Then invoke this skill again."
- If `mergeStateStatus` is not `DIRTY`, STOP with: "No merge conflicts detected. Working tree is clean."

### 3. Detect Special Cases

Before analyzing conflicts, identify files requiring special handling:

**Lock files** (package-lock.json, yarn.lock, pnpm-lock.yaml, uv.lock, Cargo.lock, Gemfile.lock, poetry.lock, go.sum, composer.lock):
- Detection: Match filename exactly
- Handling: Accept one side with `git checkout --ours/--theirs <file>`, then regenerate

**Binary files**:
- Detection: Run `git diff --numstat <file>` — binary files show `-` for both additions and deletions
- Handling: Ask user which version to keep (ours or theirs)

### 4. Analyze Text Conflicts

For each text file with conflict markers:

1. Read the file contents
2. Extract each conflict block
3. Parse conflict markers:
   - Standard 2-way: `<<<<<<< HEAD`, `=======`, `>>>>>>> branch-name`
   - diff3 style: `<<<<<<< HEAD`, `||||||| base`, `=======`, `>>>>>>> branch-name`
4. For each conflict, extract:
   - Current changes (between `<<<<<<<` and `=======` or `|||||||`)
   - Base version (between `|||||||` and `=======`, if present)
   - Incoming changes (between `=======` and `>>>>>>>`)
   - Surrounding context (5 lines before and after the conflict block)

**Structural format validation**:
After resolving conflicts in structural files, validate syntax:
- JSON: `python3 -c "import json; json.load(open('<file>'))"`
- YAML: `python3 -c "import yaml; yaml.safe_load(open('<file>'))"`
- TOML: `python3 -c "import tomllib; tomllib.load(open('<file>', 'rb'))"`

### 5. Present Conflicts

For each conflicted file, show:

**Lock files**:
| # | File | Type | Action |
|---|---|---|---|
| 1 | package-lock.json | LOCK_FILE | Regenerate with npm install |

**Binary files**:
| # | File | Type | Action |
|---|---|---|---|
| 2 | logo.png | BINARY | Choose version (ours/theirs) |

**Text conflicts** — show each conflict with context:
```
Conflict #3: src/auth.py:45

Context (5 lines before):
def authenticate(user, password):
    if not user:
        return None

    # Validate password

Current (HEAD):
    return bcrypt.check(password, user.password_hash)

Incoming (feature-branch):
    return argon2.verify(user.password_hash, password)

Context (5 lines after):

def logout(user):
    session.clear()
    return redirect('/')
```

For each text conflict, propose a resolution based on the changes and ask the user to confirm or provide an alternative.

### 6. User Confirmation

Ask the user which conflicts to resolve and how:

For **lock files**: Confirm regenerating with package manager
For **binary files**: Ask which version to keep (ours or theirs)
For **text conflicts**: For each conflict, show both sides with context and ask:
- Accept current (HEAD)
- Accept incoming (branch)
- Custom resolution (user provides the code to keep)
- Skip (leave unresolved)

The user must confirm each text conflict individually. The user can choose to:
- Resolve conflicts one by one (required for text conflicts)
- Skip any conflict to resolve manually later

If the user chooses to skip all conflicts, stop.

### 7. Apply Resolutions

For each conflict the user confirmed:

**Lock files**:
1. Choose which side to start from (usually `--theirs` to get to a valid state):
   ```bash
   git checkout --theirs <file>
   ```
2. Run the appropriate regeneration command:
   - `package-lock.json`: `npm install`
   - `yarn.lock`: `yarn install`
   - `pnpm-lock.yaml`: `pnpm install`
   - `uv.lock`: `uv lock`
   - `Cargo.lock`: `cargo update`
   - `go.sum`: `go mod tidy`
   - `Gemfile.lock`: `bundle install`
   - `composer.lock`: `composer update`
   - `poetry.lock`: `poetry lock`
3. Inform the user the lock file was regenerated

**Binary files**:
1. Apply the user's choice:
   - Ours: `git checkout --ours <file>`
   - Theirs: `git checkout --theirs <file>`

**Text conflicts**:
1. Edit the file to remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`, `|||||||` if present)
2. Apply the user's chosen resolution:
   - If accepting current (HEAD): keep the current section, remove markers
   - If accepting incoming: keep the incoming section, remove markers
   - If custom: apply the user-provided code, remove markers
3. Save the file

### 8. Post-Resolution Validation

For each resolved file:

1. **Run appropriate linter/formatter** based on file extension:
   - `.py`: `ruff format <file> && ruff check <file>`
   - `.ts`, `.tsx`, `.js`, `.jsx`: `oxfmt <file> && oxlint <file>`
   - `.rs`: `cargo fmt`
   - `.sh`: `shfmt -w <file> && shellcheck <file>`
   - `.json`: `python3 -c "import json; json.load(open('<file>'))"`
   - `.yaml`, `.yml`: `python3 -c "import yaml; yaml.safe_load(open('<file>'))"`
   - `.toml`: `python3 -c "import tomllib; tomllib.load(open('<file>', 'rb'))"`

2. **Report linter failures**: If linter or validator fails, inform the user and ask whether to keep the resolution or revert

3. **Verify no conflict markers remain in the file**:
```bash
rg "^<<<<<<< |^=======|^>>>>>>>|^\|\|\|\|\|\|\| " <file> || echo "Clean"
```

### 9. Stage Resolved Files

After resolving each file successfully, stage it:

```bash
git add <file>
```

### 10. Final Verification

Search for any remaining conflict markers across all files:

```bash
rg "^<<<<<<< " --files-with-matches
```

If any remain, list them and inform the user which conflicts still need resolution.

### 11. Summary

Present a final summary table:

| # | File | Type | Action |
|---|---|---|---|

Actions:
- `resolved` — text conflict resolved with user-chosen resolution
- `regenerated` — lock file regenerated with package manager
- `kept-ours` — binary file, kept current version
- `kept-theirs` — binary file, kept incoming version
- `skipped` — user chose to skip, left unresolved
- `failed-validation` — resolution failed linter/syntax check, reverted

If all conflicts are resolved:
```bash
git status
```

Show the user the current state and inform them they can commit the resolved conflicts.

## Edge Cases

Handle these scenarios gracefully:

- **No conflict markers found**: Even if git status shows a merge in progress, if no `<<<<<<<` markers exist, inform user "No merge conflicts detected. Working tree is clean." and stop
- **diff3 conflict style**: Handle both standard 2-way markers and diff3 3-way markers (with `|||||||` base section)
- **Lock files**: Accept one side, regenerate with package manager, never manually merge
- **Binary files**: Ask user which version to keep (ours or theirs), skip if user declines
- **Conflicts in deleted files**: Skip and inform user
- **Multiple conflicts in one file**: Present each conflict separately with surrounding context
- **Linter failures after resolution**: Report to user, ask whether to keep resolution or revert
- **User skips all conflicts**: Stop cleanly without making changes
- **JSON/YAML/TOML syntax errors after resolution**: Report failure, revert the file, ask user to resolve manually
- **Partial resolution**: Allow user to resolve some conflicts and skip others
- **PR conflicts not yet merged locally**: Detected via `gh pr view`. User is told how to surface conflicts locally (merge or rebase) and to re-invoke the skill afterward
- **No `gh` CLI available**: Skip PR conflict check and report no local conflicts found

## Important Rules

- **NEVER** auto-resolve text conflicts without user confirmation
- **NEVER** manually merge lock files — always accept one side and regenerate with the package manager
- **ALWAYS** present both sides of each text conflict with surrounding context before resolving
- **ALWAYS** verify no conflict markers remain after resolution (check for `<<<<<<<`, `=======`, `>>>>>>>`, `|||||||`)
- **ALWAYS** validate JSON/YAML/TOML syntax after resolving structural format files
- **ALWAYS** run linters/formatters after resolution (use project-specific tools: ruff for Python, oxfmt/oxlint for JS/TS)
- **ALWAYS** stage only the specific resolved files with `git add <file>` — never use `git add .` or `git add -A`
- **DO NOT** initiate merge or rebase operations — only resolve existing conflicts in the working tree
- **DO NOT** resolve conflicts in secret files (.env, credentials, etc.) without explicit user review
- If a resolution fails validation, revert and report to the user
- Support partial resolution: user can resolve some conflicts and leave others for manual handling
