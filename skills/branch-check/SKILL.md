---
name: branch-check
description: This skill should be used when the user asks to "check branch name", "validate branch name", "suggest branch name", "review branch naming", mentions "branch naming conventions", or wants to verify their git branch follows naming standards based on actual changes.
---

# Branch Name Validator

Analyze the current branch and suggest an improved name based on the actual changes.

## Context Gathering

First, gather the current state:

Current branch:
```bash
git branch --show-current
```

Determine the default base branch:
```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo main
```

Recent commits on this branch (vs base):
```bash
git log --oneline $(git merge-base HEAD <base-branch>)..HEAD
```

Changes (staged + unstaged):
```bash
git diff $(git merge-base HEAD <base-branch>)..HEAD --stat
```

Full diff summary:
```bash
git diff $(git merge-base HEAD <base-branch>)..HEAD
```

## Edge Cases

Handle these scenarios gracefully:

- **Detached HEAD**: If `git branch --show-current` returns empty, inform the user they are in detached HEAD state and this skill does not apply
- **Already on base branch**: If merge-base returns HEAD itself (diff and log are empty), inform the user there are no branch changes to analyze
- **No common ancestor**: If merge-base fails, handle gracefully and inform the user

## Analysis

Based on the commits and changes shown above:

1. **What changed**: Summarize the functional changes made in this branch (features, fixes, refactors, etc.)

2. **Suggested branch name**: Determine the best name following these conventions:
   - Format: `type/short-description`
   - Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`, `ci`, `build`
   - Use kebab-case for description
   - Keep it concise but descriptive (3-5 words max)
   - Examples: `feat/add-user-auth`, `fix/login-redirect`, `chore/update-deps`

3. **Comparison**: Compare the current branch name against your suggestion
   - If the current name is good, confirm it and explain why
   - If the current name could be improved, explain the gap

4. **Recommendation**: Provide either:
   - GOOD: Current name is appropriate (explain why)
   - SUGGESTION: Suggested improvement with reasoning

If suggesting a rename, provide the exact command:
```bash
git branch -m <current-name> <suggested-name>
```

**Note**: Only suggest a rename if there's a meaningful improvement. Don't suggest changes for minor wording preferences.
