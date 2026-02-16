---
name: labels
description: Manage GitHub repo labels and apply labels to pull requests. Use when the user asks to sync labels, suggest labels, update repo labels, or label a PR. Also use when labeling is part of a chained request (e.g., "create a PR and label it") — invoke this skill separately for the labeling step.
argument-hint: "[--sync | --pr [number]]"
---

# Manage Labels

Manage GitHub repo labels and apply labels to pull requests.

## Arguments

- No argument: list current repo labels
- `--sync`: analyze the codebase and create/update a coherent label set on the repo
- `--pr [number]`: analyze PR changes and apply appropriate labels

## Workflow: `--sync` — Sync Repo Labels

### 1. Context Gathering

Run these commands to understand the current state:

Current repo labels:
```bash
gh label list --limit 100
```

Recent commits to understand project activity:
```bash
git log --oneline -30
```

File structure to understand codebase areas:
```bash
fd --type f --max-depth 3 | head -50
```

### 2. Safety Checks

Abort in these scenarios:

- **No repo detected**: If `gh repo view` fails, STOP and inform the user they need a GitHub remote configured.
- **Not authenticated**: If gh CLI is not authenticated, STOP and instruct the user to run `gh auth login`.

### 3. Determine Repo Info

```bash
gh repo view --json owner,name --jq '.owner.login + "/" + .name'
```

### 4. Analyze and Suggest Labels

Based on the codebase analysis, suggest labels organized into categories. Use this standard scheme:

**Type labels** (map to commit types used in the project):

| Label | Color | Description |
|---|---|---|
| `type: feat` | `0e8a16` | New feature |
| `type: fix` | `d73a4a` | Bug fix |
| `type: refactor` | `1d76db` | Code restructuring |
| `type: chore` | `5319e7` | Maintenance and tooling |
| `type: docs` | `0075ca` | Documentation |
| `type: test` | `bfd4f2` | Tests |
| `type: perf` | `f9d0c4` | Performance improvement |
| `type: ci` | `e6e6e6` | CI/CD changes |
| `type: style` | `c5def5` | Formatting |
| `type: build` | `fbca04` | Build system |

**Status labels:**

| Label | Color | Description |
|---|---|---|
| `status: ready` | `0e8a16` | Ready for review |
| `status: in-progress` | `fbca04` | Work in progress |
| `status: blocked` | `d73a4a` | Blocked by dependency |

**Priority labels:**

| Label | Color | Description |
|---|---|---|
| `priority: high` | `d73a4a` | High priority |
| `priority: medium` | `fbca04` | Medium priority |
| `priority: low` | `0e8a16` | Low priority |

Additionally, suggest **area labels** based on what actually exists in the codebase (e.g., `area: api`, `area: auth`, `area: frontend`). Only suggest areas that correspond to real directories, modules, or components found during context gathering.

### 5. Present the Plan

Before making any changes:

- Show the suggested label set in a table
- Show which labels already exist and will be updated vs created new
- Show which default GitHub labels would remain (do not delete them unless asked)
- If labels already match the suggested set, inform the user labels are up to date and stop
- Ask the user to confirm before proceeding

### 6. Apply Labels

After user confirmation, create/update labels one at a time using `--force`:

```bash
gh label create "type: feat" --color "0e8a16" --description "New feature" --force
```

Run one command per label. Report results as each label is created or updated.

### 7. Verify

```bash
gh label list --limit 100
```

## Workflow: `--pr [number]` — Label a PR

### 1. Context Gathering

Get the repo's existing label set:
```bash
gh label list --limit 100
```

Determine which PR to label:
- If a number is provided: use that PR
- If no number: find the PR for the current branch:

```bash
gh pr view --json number --jq '.number' 2>/dev/null || echo "No PR found"
```

### 2. Safety Checks

Abort in these scenarios:

- **No repo detected**: If `gh repo view` fails, STOP and inform the user.
- **Not authenticated**: If gh CLI is not authenticated, STOP and instruct the user to run `gh auth login`.
- **PR not found**: If no PR exists for the current branch or the given number, STOP and inform the user.

### 3. Get PR Details

```bash
gh pr view <number> --json title,body,files,commits,labels
```

Full diff for analysis:
```bash
gh pr diff <number>
```

### 4. Analyze Changes

Look at changed files, commit messages, and diff to determine:

- **Type label** (feat, fix, refactor, etc.) — based on commit prefixes and nature of changes
- **Area labels** — based on which parts of the codebase are touched
- **Priority** — only suggest if obvious from context, otherwise skip

Do NOT suggest status labels — those are workflow-driven, not change-driven.

### 5. Present Suggestions

Before applying:

- Show which labels would be applied and the reasoning for each
- Show which labels are already on the PR
- If the PR already has the suggested labels, inform the user and stop
- Ask the user to confirm

### 6. Apply Labels

```bash
gh pr edit <number> --add-label "type: feat,area: api"
```

### 7. Verify

```bash
gh pr view <number> --json labels --jq '.labels[].name'
```

## Workflow: Default (no arguments) — List Labels

List current repo labels:

```bash
gh label list --limit 100
```

If the repo has no labels, inform the user and suggest running `--sync` to create a label set.

## Edge Cases

- **Repo has no labels**: Proceed normally with `--sync`, create from scratch
- **Labels already match**: Inform user labels are up to date, no changes needed
- **PR already labeled**: Show existing labels, ask if user wants to add or change them

## Important Rules

- **NEVER** delete labels without explicit user request
- **ALWAYS** use `--force` flag with `gh label create` to handle existing labels safely
- **ALWAYS** present the plan and ask for confirmation before creating or updating labels
- **ALWAYS** present suggested labels before applying to a PR
- **DO NOT** suggest area labels for areas that do not exist in the codebase
- **DO NOT** apply status labels automatically — those are workflow-driven
