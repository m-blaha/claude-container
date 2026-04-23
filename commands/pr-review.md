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

#### General review criteria

Apply these to every review:

- **Correctness:** Logic errors, off-by-one mistakes, unhandled edge cases, race conditions.
- **Security:** Injection vulnerabilities (SQL, command, XSS), hardcoded secrets, unsafe deserialization, improper input validation, path traversal.
- **Error handling:** Swallowed exceptions, empty catch blocks, missing cleanup on error paths. Resources (file handles, connections, child processes) must be released even on failure.
- **API contract changes:** Backward-incompatible changes to public APIs, config formats, CLI flags, or wire protocols should be intentional and documented.
- **Referenced issues:** If the PR description or commits reference issues (e.g. `Fixes #123`, `Closes #456`), fetch and read them using `gh issue view`. Verify the changes correctly and completely address each one.
- **Test coverage:** New behavior should have tests. Changed behavior should update existing tests.
- **Documentation:** User-visible changes (new commands, options, config keys, behavior changes) should be reflected in docs.
- **Commit messages:** Clear, descriptive, explain "why" when the reason isn't obvious from the diff.

#### Project-specific review guidelines

Look for a project-specific review guidelines document in the repository (e.g. `docs/pr-review-guidelines.md`, `CONTRIBUTING.md`, `docs/review-checklist.md`, or similar). If one exists, read it and apply its criteria in addition to the general ones above. Project-specific guidelines take precedence when they conflict with the general criteria.


### 6. **Report**

Provide actionable feedback organized by severity and file.
