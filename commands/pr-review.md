---
description: Review a GitHub pull request by number, or review local commits before filing a PR. Must be run from within a git repository.
---

## User Input
```text
$PR_NUMBER
```

`$PR_NUMBER` is optional. When provided, an existing GitHub PR is reviewed. When omitted, local commits on the current branch (not yet in the base branch) are reviewed instead.


## Purpose
Review code changes for correctness, security, and code quality. Provide actionable feedback. Works both for existing GitHub PRs and for local commits that haven't been pushed as a PR yet.


## Process

### 1. **Gather repo information**

Determine the `owner/repo` by parsing the `upstream` git remote URL. If no `upstream` remote exists, parse from `origin` instead:
```
git remote get-url upstream 2>/dev/null | sed 's|.*github.com[:/]\(.*\)\.git|\1|'
```

If `$PR_NUMBER` is provided, go to step 2. Otherwise, go to step 4.

---

### 2. **Fetch the PR changes** (PR number provided)

Check if the worktree has any staged or unstaged changes to tracked files (`git diff --quiet && git diff --cached --quiet`).

#### 2a. **Worktree is clean** — check out and review locally

```
gh pr checkout $PR_NUMBER --repo <owner/repo>
```

After checkout, use `gh pr diff $PR_NUMBER --repo <owner/repo>` to see the changes (always accurate regardless of local branch state). Read changed files locally for full context.

#### 2b. **Worktree is not clean** — review via GitHub API only

Do not modify the local worktree. Instead use:
```
gh pr view $PR_NUMBER --repo <owner/repo>
gh pr diff $PR_NUMBER --repo <owner/repo>
```

If you need the full content of a changed file, fetch it via the GitHub API.


---

### 3. **Review local commits** (no PR number)

Determine the base branch. Use the default branch of the repository (usually `main` or `master`):
```
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'
```
If that fails, try `main`, then `master`.

Confirm the current branch is not the base branch itself. If it is, tell the user there is nothing to review and stop.

Get the diff and full commit messages for the current branch relative to the base branch:
```
git log <base_branch>..HEAD
git diff <base_branch>...HEAD
```

If there are no commits ahead of the base branch, tell the user there is nothing to review and stop.

Read changed files locally for full context.

---

### 4. **Review**

Focus on:
- Correctness and potential bugs
- Security concerns
- Code clarity and maintainability
- Commit messages: clear, descriptive, and explain "why" when the reason isn't obvious from the diff
- If the PR description or commits reference any issues (e.g. `Fixes #123`, `Closes #456`, `Resolves owner/repo#789`), fetch and read them using `gh issue view`. Consider whether the changes correctly and completely address each referenced issue. Think about alternative approaches and compare them to the approach taken.


### 6. **Report**

Provide actionable feedback organized by severity and file.
