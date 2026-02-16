---
name: review-pr
description: Review and resolve PR review comments. Use when the user asks to handle, triage, address, or resolve PR review comments, or when asked to go through review feedback.
argument-hint: "[PR number]"
---

# Review PR Comments

Triage, validate, and resolve pull request review threads in two phases: classify each thread as valid or invalid, then fix the valid ones the user selects.

## Arguments

- No argument: review the PR for the current branch
- `<number>`: review PR with the given number

## Phase 1 — Validate Review Threads

### 1. Context Gathering

Determine repo owner and name:
```bash
gh repo view --json owner,name --jq '.owner.login + " " + .name'
```

Determine which PR to review:
- If a number is provided: use that PR
- If no number: find the PR for the current branch:

```bash
gh pr view --json number --jq '.number' 2>/dev/null || echo "No PR found"
```

Fetch the full PR diff for analysis:
```bash
gh pr diff <number>
```

### 2. Safety Checks

Abort in these scenarios:

- **No repo detected**: If `gh repo view` fails, STOP and inform the user they need a GitHub remote configured.
- **Not authenticated**: If gh CLI is not authenticated, STOP and instruct the user to run `gh auth login`.
- **PR not found**: If no PR exists for the current branch or the given number, STOP and inform the user.
- **No unresolved threads**: If the GraphQL query returns zero unresolved, non-outdated threads, inform the user there is nothing to review and STOP.

### 3. Fetch Review Threads

Use `gh api graphql` with parameterized variables to fetch all review threads:

```bash
gh api graphql -f owner='<owner>' -f repo='<repo>' -F prNumber=<number> -f query='
query($owner: String!, $repo: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          viewerCanResolve
          viewerCanReply
          comments(first: 50) {
            nodes {
              body
              diffHunk
              author {
                login
              }
            }
          }
        }
      }
    }
  }
}'
```

Filter the results: keep only threads where `isResolved` is `false` and `isOutdated` is `false`.

### 4. Team: Validation

You MUST spawn a team for this step. Do NOT classify threads yourself — delegate to the team.

Create a team and spawn these agents:

1. **explorer** (Sonnet) — Reads each thread's file at the given path and line, reads the PR diff for each affected file, and drafts a classification (VALID or INVALID) for each thread with a one-line rationale. Reports findings to the Lead via message.
2. **devil's advocate** (Opus) — Receives the explorer's classifications and challenges each one. Pushes back on dismissals that might hide real issues and on acceptances that might be style noise. Must raise at least one concern or explain why there are none.

Create tasks for each agent and assign them. Wait for both to complete before proceeding.

### 5. Classify Threads

The Lead synthesizes the explorer's context and the devil's advocate's challenges. The Lead does NOT read files or diffs directly — all context comes from the team. Each thread gets one classification:

- **VALID**: The comment raises a real issue that should be fixed (bug, logic error, missing edge case, security concern, performance issue, unclear code that needs changing)
- **INVALID**: The comment is outdated, already addressed, incorrect, based on a misreading of the code, or a style preference that conflicts with project conventions

Each classification includes a one-line rationale.

Present the classification results to the user as a table:

| # | File:Line | Comment Summary | Classification | Rationale |
|---|---|---|---|---|

Ask the user to confirm before taking any action on invalid threads.

### 6. Resolve Invalid Threads

After user confirmation, for each INVALID thread:

1. Reply with a clear explanation of why the comment is being resolved:

```bash
gh api graphql -f threadId='<id>' -f body='<explanation>' -f query='
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: $threadId,
    body: $body
  }) {
    comment { id }
  }
}'
```

2. Resolve the thread:

```bash
gh api graphql -f threadId='<id>' -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {
    threadId: $threadId
  }) {
    thread { isResolved }
  }
}'
```

If `viewerCanReply` is false for a thread, skip the reply and only resolve. If `viewerCanResolve` is false, skip resolving and only reply.

### 7. Present Valid Threads

Show a numbered table of all VALID threads:

| # | File:Line | Review Comment Summary | Proposed Fix |
|---|---|---|---|

Ask the user which threads to fix:
- `all` — fix every valid thread
- Specific numbers (e.g., `1, 3, 5`) — fix only those
- `none` — stop here

If the user chooses `none` or there are no valid threads, stop.

## Phase 2 — Fix Chosen Threads

### 8. Team: Implementation

You MUST spawn a team for this step. Do NOT apply fixes yourself — delegate to the team.

Spawn these agents (reuse the existing team if still active):

1. **implementer** (Sonnet) — One task per chosen thread. Reads the file, applies the fix, runs linters and type-checkers relevant to the file type.
2. **devil's advocate** (Opus) — Reviews each fix to ensure it addresses the feedback without introducing regressions or over-engineering. Must raise at least one concern or explain why there are none.

Create tasks for each agent and assign them. Wait for both to complete before proceeding.

### 9. Post-Fix

For each fixed thread:

1. Reply confirming the change was applied:

```bash
gh api graphql -f threadId='<id>' -f body='<confirmation>' -f query='
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: $threadId,
    body: $body
  }) {
    comment { id }
  }
}'
```

2. Resolve the thread:

```bash
gh api graphql -f threadId='<id>' -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {
    threadId: $threadId
  }) {
    thread { isResolved }
  }
}'
```

If `viewerCanReply` is false, skip the reply and only resolve. If `viewerCanResolve` is false, skip resolving and only reply.

### 10. Summary

Present a final summary table of all actions taken:

| # | File:Line | Comment Summary | Action |
|---|---|---|---|

Actions: `resolved-invalid`, `fixed`, `skipped`.

## Edge Cases

- **No unresolved threads**: Inform the user there is nothing to review and stop
- **All threads are outdated**: Inform the user all threads are outdated, skip them, and stop
- **User chooses none to fix**: Stop after resolving invalid threads
- **Thread on deleted file**: Mark as outdated, skip it, and inform the user
- **viewerCanResolve is false**: Skip resolving, only reply with an explanation
- **viewerCanReply is false**: Skip replying, only resolve
- **Both viewerCanResolve and viewerCanReply are false**: Skip the thread entirely and inform the user

## Important Rules

- **NEVER** resolve a thread without replying with an explanation first (unless `viewerCanReply` is false)
- **NEVER** auto-fix without user confirmation
- **ALWAYS** use parameterized GraphQL variables — no string interpolation in queries
- **ALWAYS** present the classification results before taking any action on invalid threads
- **ALWAYS** ask user confirmation before resolving invalid threads
- **ALWAYS** ask user which valid threads to fix before starting implementation
- **DO NOT** process outdated or already-resolved threads
- **ALWAYS** spawn a team for validation (Step 4) and implementation (Step 8) — never classify threads or apply fixes directly
