---
description: Review a GitHub pull request by number. Must be run from within a git repository.
---

## User Input
```text
$PR_NUMBER
```

## Purpose
Review a GitHub pull request for correctness, security, and code quality. Provide actionable feedback.


## Process

### 1. **Gather repo information**

Determine the `owner/repo` by parsing the `upstream` git remote URL. If no `upstream` remote exists, parse from `origin` instead:
```
git remote get-url upstream 2>/dev/null | sed 's|.*github.com[:/]\(.*\)\.git|\1|'
```

Check if the worktree has any staged or unstaged changes to tracked files (`git diff --quiet && git diff --cached --quiet`).


### 2a. **Worktree is clean** — check out and review locally

```
gh pr checkout $ARGUMENTS --repo <owner/repo>
```

After checkout, use `gh pr diff $ARGUMENTS --repo <owner/repo>` to see the changes (always accurate regardless of local branch state). Read changed files locally for full context.


### 2b. **Worktree is not clean** — review via GitHub API only

Do not modify the local worktree. Instead use:
```
gh pr view $ARGUMENTS --repo <owner/repo>
gh pr diff $ARGUMENTS --repo <owner/repo>
```

If you need the full content of a changed file, fetch it via the GitHub API.


### 3. **Check referenced issues**

If the PR description or commits reference any issues (e.g. `Fixes #123`, `Closes #456`, `Resolves owner/repo#789`), fetch and read them using `gh issue view`. Consider whether the PR correctly and completely addresses each referenced issue. Think about alternative approaches to solving the issue and compare them to the approach taken in the PR.


### 4. **Review**

Focus on:
- Correctness and potential bugs
- Security concerns
- Code clarity and maintainability
- Commit messages: clear, descriptive, and explain "why" when the reason isn't obvious from the diff


### 5. **Report**

Provide actionable feedback organized by severity and file.
