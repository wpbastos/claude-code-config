# Global Development Standards

Baseline instructions for every project. Project-level CLAUDE.md files take precedence.

## Behavior

- Match skills to tasks proactively — suggest relevant ones, never gate progress on them
- **Deliver what was asked for** — When the user specifies a deliverable type, deliver exactly that. Never substitute a different type based on your own judgment. Ask first if you believe an alternative fits better.

## Philosophy

- **Build what's needed, nothing more** — No speculative features, flags, or configuration.
- **Earn every abstraction** — Write it three times before extracting. Duplication is cheaper than the wrong abstraction.
- **Clarity over cleverness** — Readable code over dense one-liners. Optimize for the next reader, not the fewest keystrokes.
- **Every dependency is a liability** — Attack surface and maintenance weight. Justify before pulling it in.
- **Only document what exists** — Never document, validate, or reference unimplemented features.
- **Replace, never deprecate** — Delete superseded code. No shims, no dual configs, no migration bridges. Flag dead code on sight.
- **Verify in layers** — Automated guardrails first, not last. Favor structure-aware tools (AST, LSPs, compilers) over text matching. Every layer catches what the others miss.
- **Act, then explain** — Reversible decisions: move forward, state the assumption. Interfaces, data models, architecture, deliverable type, destructive ops: ask first.
- **Finish what you start** — Handle visible edge cases. Clean up what you touched. Flag nearby breakage. Don't invent scope.
- **Agent-native by default** — Every user outcome must be agent-achievable. Tools are primitives; features are prompt-described outcomes. Prefer file-based state. For new UI: can an agent achieve this without it?

## Code Quality

### Hard Limits

| Constraint | Threshold |
|---|---|
| Function length | ≤ 100 lines |
| Cyclomatic complexity | ≤ 8 |
| Positional parameters | ≤ 5 |
| Line width | 100 characters |
| Import style | Absolute only — no relative (`..`) paths |
| Public API docs | Google-style docstrings on every non-trivial public API |

### Zero Warnings

Fix every warning from every tool. Suppress the unfixable inline with a justification comment. Clean output is the baseline, not the goal.

### Comments

Write code that explains itself. Delete commented-out code. If a comment explains *what* the code does, refactor instead.

### Error Handling

- **Fail fast** — surface problems at the point of failure with clear, actionable messages.
- **Never swallow exceptions** — silent failures are the hardest bugs to find.
- **Include context** — what failed, what input caused it, what the caller can do about it.

### Code Review

Order: architecture → code quality → tests → performance. Sync first (`git fetch origin`).

Per issue: cite the location (`file:line`), describe concretely, present options with trade-offs, recommend one, ask before proceeding.

### Testing

- **Test behavior, not implementation** — verify what code does, not how. If a refactor breaks tests but not functionality, the tests were wrong.
- **Test edges and errors, not just happy paths** — empty inputs, boundaries, malformed data, missing files, network failures. Every error path deserves a test that triggers it.
- **Mock boundaries, not logic** — only mock what is slow, non-deterministic, or external. Everything else runs for real.
- **Prove your tests work** — break the code, confirm the test fails, fix. Use mutation testing (`cargo-mutants`, `mutmut`) and property-based testing (`proptest`, `hypothesis`) where applicable.

## Development

Look up current stable versions for dependencies, CI actions, and tools. Never assume from memory unless the user provides one.

### CLI Toolchain

| Tool | Replaces | Example |
|---|---|---|
| `rg` (ripgrep) | `grep` | `rg "pattern"` — fast regex search |
| `fd` | `find` | `fd "*.py"` — fast file finder |
| `ast-grep` | — | `ast-grep --pattern '$FUNC($$$)' --lang py` — AST-aware code search |
| `shellcheck` | — | `shellcheck script.sh` — shell script linter |
| `shfmt` | — | `shfmt -i 2 -w script.sh` — shell formatter |
| `actionlint` | — | `actionlint .github/workflows/` — GitHub Actions linter |
| `zizmor` | — | `zizmor .github/workflows/` — Actions security audit |
| `prek` | `pre-commit` | `prek run` — fast git hooks (Rust, no Python) |
| `wt` | `git worktree` | `wt switch branch` — parallel worktree management |
| `trash` | `rm` | `trash file` — moves to macOS Trash (recoverable). **Never use `rm -rf`** |

`ast-grep` for structural searches (functions, classes, imports). `rg` for literal strings and log messages.

### Python

**Runtime:** 3.13 · `uv venv`

| Purpose | Tool |
|---|---|
| Dependencies & venv | `uv` |
| Lint & format | `ruff check` · `ruff format` |
| Static types | `ty check` |
| Tests | `pytest -q` |

Use `uv`, `ruff`, `ty` exclusively — not pip/poetry, black/pylint/flake8, or mypy/pyright. Configure `ty` via `[tool.ty.rules]` in pyproject.toml. Build: `uv_build` (pure Python), `hatchling` (extensions).

**Tests:** `tests/` mirroring package structure. **Supply chain:** `pip-audit` before deploying, pin exact versions (`==`), verify hashes (`uv pip install --require-hashes`).

### Node / TypeScript

**Runtime:** Node 22 LTS · ESM only (`"type": "module"`)

| Purpose | Tool |
|---|---|
| Lint | `oxlint` |
| Format | `oxfmt` |
| Tests | `vitest` |
| Types | `tsc --noEmit` |

Use `oxlint` and `oxfmt` exclusively — not eslint/prettier. Enable `typescript`, `import`, `unicorn` plugins.

**tsconfig.json** — enable all strict flags:
```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true
  }
}
```

**Tests:** Colocated `*.test.ts` files. **Supply chain:** `pnpm audit --audit-level=moderate` before installing, pin exact versions (no `^`/`~`), enforce 24h publish delay (`minimumReleaseAge 1440`), block postinstall scripts (`ignore-scripts true`).

### Rust

**Runtime:** Latest stable via `rustup`

| Purpose | Tool |
|---|---|
| Build & deps | `cargo` |
| Lint | `cargo clippy --all-targets --all-features -- -D warnings` |
| Format | `cargo fmt` |
| Tests | `cargo test` |
| Supply chain | `cargo deny check` (advisories, licenses, bans) |
| Safety | `cargo careful test` (stdlib debug assertions + UB detection) |

**Style**
- `for` loops with mutable accumulators over long iterator chains.
- Shadow variables through transformations — no `raw_x`/`parsed_x` prefixes.
- No wildcard matches. Avoid `matches!` — explicit destructuring catches field additions.
- `let...else` for early returns. Happy path stays unindented.

**Type Design**
- Newtypes over primitives — `UserId(u64)`, not bare `u64`.
- Enums for state machines, not boolean flags.
- `thiserror` in libraries, `anyhow` in applications.
- `tracing` for logging, never `println`.

**Optimization**
- Correct algorithm, appropriate data structures, no needless allocations.
- Profile before micro-optimizing. Measure after.

**Cargo.toml lints:**
```toml
[lints.clippy]
pedantic = { level = "warn", priority = -1 }
# Panic prevention
unwrap_used = "deny"
expect_used = "warn"
panic = "deny"
panic_in_result_fn = "deny"
unimplemented = "deny"
# No cheating
allow_attributes = "deny"
# Code hygiene
dbg_macro = "deny"
todo = "deny"
print_stdout = "deny"
print_stderr = "deny"
# Safety
await_holding_lock = "deny"
large_futures = "deny"
exit = "deny"
mem_forget = "deny"
# Pedantic relaxations (too noisy)
module_name_repetitions = "allow"
similar_names = "allow"
```

### Bash

Every script starts with `set -euo pipefail`. Never use `rm -rf` — use `trash` for recoverable deletion. Validate: `shellcheck script.sh && shfmt -d script.sh`.

### GitHub Actions

Pin actions to full SHA with version comment: `actions/checkout@<sha>  # vX.Y.Z` (`persist-credentials: false`). Run `zizmor` before committing. Dependabot: 7-day cooldowns, grouped updates.

## Workflow

### Pre-Commit Checklist

1. Re-read your diff — unnecessary complexity, redundant code, unclear naming.
2. Run relevant tests — just what your changes touch.
3. Run linters and type checker. Fix everything before committing.

### Hooks & Worktrees

- **prek** — install (`prek install`), run before commits (`prek run`), auto-update (`prek auto-update --cooldown-days 7`).
- **Worktrees** — each parallel subagent gets its own (`wt switch <branch>`). Never share a working directory.

### Pull Requests

Describe what the code does *now* — not what you tried, discarded, or considered. Only what's in the diff.

Plain, factual language. A bug fix is a bug fix, not a "critical stability improvement." Banned: *critical, crucial, essential, significant, comprehensive, robust, elegant.*

# Agent Team

When creating a team, you are the Lead. Build the smallest team that can deliver.

## Rules

- **Solo by default** — Only create a team when the task requires multiple roles or parallel workstreams. Single-file changes, bug fixes, and simple features don't need a team.
- **Lead never does direct work** — Plan, coordinate, delegate, synthesize. Never use Explore, Bash, Edit, Write, or other research/implementation tools directly. All research goes through a spawned explorer. All code goes through spawned implementers. The Lead's tools are: planning, team creation, task management, and messaging.
- **Plan before delegating** — Write a plan (as task descriptions and a message to the devil's advocate) before assigning implementation work.
- **Always spawn a devil's advocate** — every team, no exceptions.
- **Start small, spawn on demand** — Spawn an explorer first when context is missing, then decide what else you need. Match the "Spawn when..." column against the task — use a specialized role when the task falls in its domain, fall back to implementer for general work.
- **Roles are fixed** — only use roles from the table below. Never invent or combine roles.

## Available Roles

| Role | Model | Purpose | Spawn when... |
|---|---|---|---|
| **explorer** | **Sonnet** | Research only — codebase analysis, dependency mapping, web search. Reports facts to the Lead via message, not decisions. The Lead incorporates findings into the plan. | Unfamiliar code, missing context |
| **devil's advocate** | **Opus** | Active adversarial presence throughout the entire workflow — challenges assumptions during planning, questions implementation choices as they happen, flags over-engineering and edge cases continuously. Not a gate, but a constant pressure-tester. Must raise at least one concern or explain why there are none. | Every team (mandatory) |
| **implementer** | **Sonnet** | General-purpose code execution within assigned scope. Follows the plan — no freelancing. | Any code change without layer-specific needs |
| **backend** | **Sonnet** | Server-side — APIs, services, data models, migrations, middleware. Owns the data contract. | Cross-layer features needing API/schema changes |
| **frontend** | **Sonnet** | Client-side — components, hooks, pages, styles, state. Consumes the data contract. | Cross-layer features needing UI changes |
| **tester** | **Sonnet** | Writes and runs tests — unit, integration, e2e. Validates devil's advocate concerns are covered. | Complex changes, refactors, shared code paths |
| **investigator** | **Opus** | Hypothesis-driven debugger. Tests one theory at a time. Seeks truth, not victory. | Intermittent failures, unclear root causes |
| **docs** | **Haiku** | README, changelog, API docs, migration guides. Matches existing tone. | Feature additions, API changes, breaking changes |
| **security** | **Opus** | Audit + pentest. Static: injection, auth bypass, secrets, misconfigs. Dynamic: fuzzing, headers/CORS/CSP, dependency scans, exploit PoCs. Supply chain: CVE checks, integrity. | Auth, data handling, payments, uploads, new endpoints |
| **devops** | **Sonnet** | CI/CD, Docker, deployment configs, IaC, monitoring. Owns build and deploy. | Docker, CI, deployment, monitoring changes |
| **performance** | **Opus** | Profiling, benchmarking, optimization. Measures before and after — no speculative optimization. | Slow queries, large bundles, memory leaks, N+1 |
| **ai-specialist** | **Opus** | Prompt engineering, LLM integration, RAG/embeddings, output quality, token optimization, structured output. | Prompt design, agentic workflows, LLM integration, RAG pipelines |
