# Claude Code Configuration

A ready-to-use configuration for Claude Code development. Clone directly into
`~/.claude` to establish development standards, workflow automation, and safety
guardrails.

Inspired by
[trailofbits/claude-code-config](https://github.com/trailofbits/claude-code-config).

## Prerequisites

These tools are referenced in `CLAUDE.md` and used across workflows.

### Core CLI Tools

| Tool | Replaces | Description |
|------|----------|-------------|
| `rg` (ripgrep) | `grep` | Fast regex search |
| `fd` | `find` | Fast file finder |
| `ast-grep` | — | AST-aware code search |
| `shellcheck` | — | Shell script linter |
| `shfmt` | — | Shell formatter |
| `actionlint` | — | GitHub Actions linter |
| `zizmor` | — | GitHub Actions security audit |
| `prek` | `pre-commit` | Fast git hooks (Rust-based) |
| `wt` (worktrunk) | `git worktree` | Parallel worktree management |
| `trash` (macos-trash) | `rm` | Recoverable file deletion (moves to macOS Trash) |

```bash
brew install ripgrep fd ast-grep shellcheck shfmt \
  actionlint zizmor macos-trash
cargo install prek worktrunk
```

### Python

Runtime: Python 3.13

| Tool | Purpose |
|------|---------|
| `uv` | Package manager, venv, dependency resolution |
| `ruff` | Linter and formatter |
| `ty` | Static type checker |
| `pytest` | Test runner |
| `pip-audit` | Dependency vulnerability scanner |

```bash
brew install uv
uv tool install ruff
uv tool install ty@latest
uv tool install pytest
uv tool install pip-audit
```

### Node / TypeScript

Runtime: Node 22 LTS

| Tool | Purpose |
|------|---------|
| `oxlint` | Linter (replaces ESLint) |
| `oxfmt` | Formatter (replaces Prettier) |
| `tsc` | TypeScript compiler and type checker |
| `vitest` | Test runner |

```bash
brew install node@22
npm install -g oxlint
```

Per-project installs:
```bash
npm install -D typescript  # includes tsc
npm install -D oxfmt       # alpha, not stable for global use
npm install -D vitest
```

### Rust

| Tool | Purpose |
|------|---------|
| `cargo` | Build system and package manager |
| `cargo-deny` | License, advisory, and ban checking |
| `cargo-careful` | UB detection with stdlib debug assertions |

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install --locked cargo-deny cargo-careful
```

## Installation

Clone this repository directly into your Claude Code config directory:

```bash
git clone <repo-url> ~/.claude
```

That's it. No copying, moving, or manual setup needed. The `.gitignore` uses a
whitelist approach — only tracked files are shipped; anything Claude Code
creates at runtime is automatically ignored.

## What's Included

### CLAUDE.md

Global development standards covering:
- Philosophy (build what's needed, earn every abstraction, clarity over
  cleverness)
- Code quality hard limits (function length, complexity, line width, imports)
- Language-specific tools and standards for Python, Node, Rust, and Bash
- Testing strategy (test behavior, not implementation; test edges and errors)
- Agent team rules with devil's advocate role requirements
- Pull request and commit conventions

Create project-specific overrides by adding a `CLAUDE.md` to your project repo.

### settings.json

Claude Code configuration including:
- Environment variables (team name, effort level, telemetry settings)
- Permissions matrix (allowed/denied operations for git, bash, file access)
- Safety allowlist for python scripts, pytest, npm/node commands
- Secret file blocking (prevents reading `.env`, `.ssh`, credentials, keys)
- Destructive command blocking (no `rm -rf`, `dd`, force pushes)
- Status line configuration
- Plugin enablement (context7, github, playwright)

### Skills

Ready-to-use git workflow skills:

- **branch-check**: Validate branch names against conventions and suggest
  improvements based on actual changes
- **commit**: Create git commits following project conventions with proper
  message formatting
- **create-pr**: Create pull requests with structured summaries and test plans
- **review-pr**: Triage, validate, and resolve PR review comments
- **labels**: Manage repo labels and apply labels to pull requests
- **resolve-conflicts**: Resolve merge conflicts interactively

Each skill is documented in its own `SKILL.md` with usage instructions.

### Hooks

#### block-destructive.py

PreToolUse hook that blocks dangerous bash patterns before execution:
- Filesystem destruction (`rm -rf /`, `rm -rf ~`)
- Disk operations (`dd`, `mkfs`, `fdisk`)
- Fork bombs and suspicious redirects
- Credential exfiltration attempts
- Code injection patterns

The hook runs automatically on all bash commands and returns explicit deny
decisions for blocked patterns.

### Pre-commit Configuration

Configured via `prek.toml`:
- Trailing whitespace removal
- End-of-file fixing
- Large file detection
- JSON validation
- Ruff linting and formatting

Run pre-commit hooks with:

```bash
prek run
```

### Pull Request Template

GitHub pull request template (`.github/PULL_REQUEST_TEMPLATE.md`) with:
- Summary section for change description
- Type of change checkbox (feat, fix, refactor, etc.)
- Test plan section

## Configuration

### Environment Variables

Key settings from `settings.json`:

| Variable | Value | Purpose |
|---|---|---|
| `CLAUDE_CODE_TEAM_NAME` | `iceberg` | Default team name for agent coordination |
| `CLAUDE_CODE_EFFORT_LEVEL` | `high` | Agent reasoning effort level |
| `CLAUDE_CODE_SUBAGENT_MODEL` | `sonnet` | Model for spawned agents |
| `DISABLE_TELEMETRY` | `1` | Disable usage telemetry |
| `DISABLE_ERROR_REPORTING` | `1` | Disable error reporting |

Full customization available in `settings.json`.

### Status Line

The status line (via `statusline.py`) displays:
- Current model
- Directory (repo-aware)
- Git branch with staged and modified file counts (cached for performance)
- Context progress bar (color-coded: green for low, yellow for moderate, red
  for high usage)
- Cost estimate
- Token counts (input and output)
- Session duration
- Lines added/removed
- Cache hit percentage

Git state is cached for 5 seconds to avoid repeated system calls.

### Permissions

Permissions are defined as patterns. Allowed operations include:
- Git queries (status, log, branch, diff, remote)
- GitHub CLI (pr/issue viewing, label listing)
- Python/Node/Maven/Gradle commands
- File listing and directory operations
- Basic commands (pwd, cd, echo, cat)

Explicitly denied:
- Secrets files (`.env`, `.ssh`, credentials, keys, cloud configs)
- Destructive git (force push, hard reset, branch deletion)
- Destructive filesystem (rm -rf, mkfs, dd)
- Code injection patterns (curl/wget piping to bash)

### Hooks

Pre-execution hooks are configured in `settings.json` to run `block-destructive.py`
on all bash commands. Hooks can be customized by editing the `hooks` section.

## Customization

### Extending CLAUDE.md

Override or extend standards for a specific project by adding `CLAUDE.md` to
the project root. Project-level settings take precedence over global ones.

### Adding Skills

Create a new skill by adding a directory to `skills/` with:
1. A `SKILL.md` file describing the skill and its workflow
2. Optional scripts in a `scripts/` subdirectory

Skills are automatically discovered by Claude Code.

### Modifying Hooks

Edit `hooks/block-destructive.py` to adjust the blocked pattern list or add
new safety checks. Modify the `BLOCKED_PATTERNS` list to customize behavior.

### Adjusting Permissions

Edit `settings.json` to:
- Allow new bash commands in the `permissions.allow` list
- Deny additional file patterns in the `permissions.deny` list

## Using with Teams

This configuration sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to enable agent
team functionality. Teams coordinate through task lists and messaging, with the
devil's advocate role providing continuous challenge to plans and implementations.

See `CLAUDE.md` for agent team rules and available roles.
