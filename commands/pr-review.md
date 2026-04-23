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

Focus on the following areas, organized by priority.

#### Critical — likely to block merge

- Correctness and potential bugs
- Security concerns
- ABI/API stability: Adding or modifying public methods in `libdnf5` or `libdnf5-cli` headers requires a version bump in `VERSION.cmake` and `dnf5.spec`. Changing access modifiers (e.g., `private` to `public`) can also break ABI. Check whether the change introduces or modifies anything in a public header.
- Allocation failure handling: When calling C libraries (especially libxml2, librpm, libcurl), check that NULL return values are handled. Prefer throwing `std::bad_alloc` over silently skipping.
- Error handling and propagation: Exceptions in `libdnf5` must be properly typed. Empty `catch` blocks and swallowed errors should be flagged. Resource cleanup (e.g., `waitpid`, file descriptors) must happen even on exception paths — prefer RAII / scope-exit patterns.
- Thread safety: File locking for shared state, concurrent access to repositories, zombie process prevention. Check that `waitpid` is called in destructors, and that `fsync` covers both file and directory.
- If the PR description or commits reference any issues (e.g. `Fixes #123`, `Closes #456`, `Resolves owner/repo#789`), fetch and read them using `gh issue view`. Consider whether the changes correctly and completely address each referenced issue. Think about alternative approaches and compare them to the approach taken.

#### Important — should be addressed

- License headers: New files must use `LGPL-2.1-or-later`. Use the short SPDX header format:
  ```
  // Copyright Contributors to the DNF5 project
  // SPDX-License-Identifier: LGPL-2.1-or-later
  ```
  If a file uses a different license, verify it is intentional and consistent with its directory.
- Documentation: Man pages (`doc/` RST files) must be updated when commands, options, or user-visible behavior change. JSON output schemas should be documented in the man page. Document replaceable elements as uppercase (e.g., `PATH` not `<path>`).
- Internationalization: All user-facing strings in the CLI must be translatable via gettext. `libdnf5` must not print to stderr — use logger or exceptions instead.
- Spec file: When new files, subpackages, man pages, or directories are added, check that they are listed in the `%files` section of `dnf5.spec`. Ghost directories need `%attr` and `%ghost %dir` entries.
- Naming consistency: Use `--srpm` not `--source`, `--arch` not `--archs`, "OpenPGP" not "GPG", `user-installed` not `user installed`. Variable names should be descriptive (`n_read` not `n`).
- Code clarity and maintainability
- Commit messages: clear, descriptive, and explain "why" when the reason isn't obvious from the diff. Multiple cleanup commits should be squashed. If AI tools were used, add a trailer (e.g., `Assisted-by: GitHub Copilot`).

#### Suggestions — non-blocking improvements

- Code sharing: If logic is duplicated between `dnf5` CLI and `libdnf5` (or between plugins), suggest moving shared code into `libdnf5`. Consider filing a follow-up issue rather than blocking the PR.
- Const correctness: Function parameters should be `const &` where possible to avoid unnecessary copies. Use `std::move` for transferring ownership.
- Performance: Suggest `reserve()` for vectors when size is known, `emplace_back` over `push_back`.
- JSON output design: Keys should be lowercase with underscores. Timestamps should use UNIX epoch format. Empty sections should still be present in output for parsability.
- Test coverage: Suggest CI tests (ci-dnf-stack behave tests) for new commands/features. For public API changes, suggest Python unit tests. Note unrelated CI failures explicitly.

#### Review tone

This team has a collaborative review culture. Reviewers frequently approve with inline nitpicks rather than requesting changes. When flagging non-blocking issues, say "This could be improved in a follow-up PR" rather than blocking the merge.


### 6. **Report**

Provide actionable feedback organized by severity and file.
