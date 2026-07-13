---
description: Test-driven bugfix workflow for dnf5 using the dev container
---

You have access to a Fedora dev container with all dnf5 build dependencies.
`dnf5-configure`, `dnf5-build`, `dnf5-test`, `dnf5-exec` are bash commands on your PATH.

Execute this workflow directly — do not enter plan mode. Follow the steps strictly
in the exact order listed. Do not skip or reorder steps.

## Arguments

The user's input may include `--attempts=N` (e.g. `--attempts=3`). This controls how
many independent fix attempts to run in parallel. Default is 1.

- `--attempts=1` (default): standard single-pass workflow
- `--attempts=N` (N > 1): ensemble mode — run N independent attempts, then synthesize

## Workflow order (mandatory)

**Standard mode (attempts=1):**

1. Understand the bug
2. Write a reproducer (test that captures the bug)
3. Validate test expectations against the domain model
4. RED — build and confirm the reproducer test FAILS
5. Evaluate alternative fix approaches, choose the best one
6. Implement the chosen fix
7. GREEN — build and confirm the test PASSES with the fix
8. Regression check — run full test suite
9. Create commits
10. Report

**Ensemble mode (attempts > 1):**

1. Understand the bug
2. Write a reproducer (test that captures the bug)
3. Validate test expectations against the domain model
4. RED — build and confirm the reproducer test FAILS
5. Collect reproducer artifacts
6. Parallel fix attempts (spawn N agents)
7. Synthesize the best fix
8. Regression check — run full test suite
9. Create commits
10. Report

## Step 1: Understand the bug

Read the bug report (issue, Bugzilla, or user description). Identify:
- What is the expected behavior?
- What is the actual (broken) behavior?
- What packages, repositories, or configuration trigger it?

Search the codebase for the relevant code path. Identify the component (libdnf5, dnf5 CLI,
plugin, daemon, etc.) and the specific functions involved.

## Step 2: Write a reproducer

Choose the appropriate approach based on the bug:

### Option A: Unit/integration test (preferred when possible)

Use the existing test framework. Tests live in `test/` and use `BaseTestCase` from
`test/shared/base_test_case.hpp` (C++) or `test/python3/libdnf5/base_test_case.py` (Python).

1. If you need custom packages, create `.spec` files in `test/data/repos-rpm/<repo-id>/`:

```spec
Name:       testpkg
Version:    1.0
Release:    1
Summary:    Test package for bug reproduction
License:    MIT
Architecture: noarch

%description
Test package.

%install
mkdir -p %{buildroot}/usr/share/testpkg
echo "test" > %{buildroot}/usr/share/testpkg/file.txt

%files
/usr/share/testpkg/file.txt
```

2. Write a test case that loads the repo and triggers the bug:

```cpp
// test/libdnf5/<area>/test_bugname.cpp
void BugNameTest::setUp() {
    BaseTestCase::setUp();
    add_repo_rpm("my-test-repo");
}

void BugNameTest::test_reproduces_bug() {
    // Trigger the buggy behavior
    // Assert the EXPECTED (correct) behavior — this should FAIL before the fix
}
```

3. Build test packages and run:

```bash
dnf5-build build_rpm_and_repos
dnf5-build
dnf5-test -R test_bugname
```

### Option B: Behavioral test (ci-dnf-stack)

When the bug requires a full dnf5 invocation (transaction handling, CLI behavior,
repo interaction, etc.), write a Behave scenario in ci-dnf-stack.

The ci-dnf-stack repo is at `$SRC_DIR/ci-dnf-stack/` and uses git worktrees (same
layout as dnf5). Read existing `.feature` files in `main/dnf-behave-tests/dnf/` for
patterns and available step definitions (in `dnf-behave-tests/dnf/steps/`).

1. Create a new worktree for this bug (use the bug/issue ID as the branch name):

```bash
git -C $SRC_DIR/ci-dnf-stack/main worktree add \
    $SRC_DIR/ci-dnf-stack/<bug-id> -b <bug-id>
```

2. Ensure test fixtures are built in the new worktree:

```bash
dnf5-exec bash -c "cd $SRC_DIR/ci-dnf-stack/<bug-id>/dnf-behave-tests && fixtures/specs/build.sh"
```

3. If you need custom test packages, create spec files in
   `$SRC_DIR/ci-dnf-stack/<bug-id>/dnf-behave-tests/fixtures/specs/<repo-name>/`
   and rebuild fixtures.

4. Write a `.feature` file using Gherkin syntax. Example pattern:

```gherkin
Feature: Bug description

Background: Set repositories
  Given I use repository "simple-base"

# <full bug URL, e.g. https://github.com/rpm-software-management/dnf5/issues/1234>
Scenario: Describe the expected behavior
 When I execute dnf with args "install <package>"
 Then the exit code is 0
  And Transaction is following
      | Action  | Package                        |
      | install | package-0:1.0-1.fc29.x86_64    |
```

Common steps (see `dnf-behave-tests/dnf/steps/` for all available):
- `Given I use repository "<name>"` — activate a test repo
- `When I execute dnf with args "<args>"` — run dnf5 with arguments
- `Then the exit code is <N>` — check exit code
- `And Transaction is following` — verify transaction table
- `Then stdout contains "<text>"` / `Then stderr contains "<text>"`

5. Run the scenario against the locally-built dnf5:

```bash
dnf5-exec bash -c "cd $SRC_DIR/ci-dnf-stack/<bug-id>/dnf-behave-tests && behave -Ddnf_command=$DNF5_SRC_DIR/build-dev/dnf5/dnf5 dnf/<feature_file>.feature"
```

6. Verify the bug is reproduced (test should fail before the fix).

## Step 3: Validate test expectations

Before running the reproducer, critically review every assertion in it. For each asserted
value, ask: "Is this value knowable from the inputs, or am I fabricating information?"

- If reusing an `@xfail`, `XFAIL`, or pre-existing failing test, treat every assertion as
  a claim that needs justification — not as a specification to implement against.
  Speculative tests describe what someone wished would happen, not what should happen.
- Trace each expected value back to the concrete inputs (packages, repos, config). If you
  cannot justify an assertion from the domain model, remove or fix it.
- Pay special attention to values that "look right" but have no source: repo names for
  locally-installed packages, version strings for packages that were never in a repo, etc.

## Step 4: RED — confirm the reproducer test fails

Run the reproducer and confirm it demonstrates the broken behavior.
If the test passes, the reproducer doesn't capture the bug — revise it.

```bash
dnf5-build
dnf5-test -R test_bugname
```

Report: "Test fails as expected: [describe the failure]"

## Step 5: Evaluate fix approaches

Now that the bug is confirmed and the failing test reveals the root cause, identify
alternative ways to fix it. For each, consider:
- Correctness: does it fully fix the bug, including edge cases?
- Scope: how many files/components does it touch?
- Risk: could it break existing behavior or ABI/API?
- Maintainability: is the fix easy to understand and maintain?

Choose the approach with the best balance of correctness, minimal scope, and lowest risk.
Document your reasoning briefly in the final report.

## Step 6: Fix the bug

Implement the chosen approach. Keep the change minimal — fix only the bug, don't refactor.

## Step 7: GREEN — confirm the fix makes the test pass

```bash
dnf5-build
dnf5-test -R test_bugname
```

If it still fails, iterate on the fix. Do not proceed until the test passes.

Report: "Test passes after fix."

## Step 8: Regression check — run full test suite

```bash
dnf5-test
```

If any other tests fail, investigate whether the fix caused a regression.
Fix regressions before reporting success.

## Step 9: Create commits

Create a logical set of commits. The structure depends on the reproducer approach:

**If Option A was used (unit test in dnf5 repo):**
1. Test commit: spec files (if any) + test case
2. Fix commit: the code change

**If Option B was used (ci-dnf-stack behavioral test):**
1. In the dnf5 repo: fix commit(s) only
2. In the ci-dnf-stack worktree (`$SRC_DIR/ci-dnf-stack/<bug-id>`): commit the
   `.feature` file and any new spec files/fixtures

If the fix touches multiple independent areas, split into separate commits per area.

Commit message format — follow the project's existing style from `git log`. Typically:
- First line: short summary (imperative mood)
- Blank line, then body explaining the root cause and what the fix changes
- Reference the bug/issue if applicable

All commits must include a Signed-off-by line from the current git user. Use `git commit -s`
or add `Signed-off-by: <name> <email>` (from `git config user.name` / `git config user.email`)
to the commit message.

## Step 10: Report

Summarize:
- Root cause of the bug
- What the fix changes
- How the bug was reproduced
- Full test suite result
- Commits created

---

# Ensemble mode steps (only when attempts > 1)

Steps 1–4 are identical to standard mode. The following steps replace steps 5–10.

## Ensemble step 5: Collect reproducer artifacts

After confirming RED, collect everything the parallel agents will need:

1. **Bug summary**: a self-contained description of the bug (expected vs actual behavior,
   component, relevant code paths) — write it so a reader with no prior context can understand.
2. **Reproducer files**: for each new or modified file (test cases, spec files, CMakeLists
   changes), record the absolute path and full content.
3. **Test filter**: the exact ctest `-R` filter or behave command that runs the reproducer.
4. **Failing output**: the test output from step 4 showing the failure.

## Ensemble step 6: Parallel fix attempts

Spawn N agents in a **single message** (so they run concurrently). Use the `Agent` tool
with `isolation: "worktree"` for each. Every agent prompt must be fully self-contained —
agents have no context from this conversation.

The worktree already contains the reproducer files (committed or staged before spawning).
Agents do NOT need to build or run tests — RED was confirmed in step 4, and GREEN will
be verified once on the final synthesized fix in step 7.

Each agent prompt must include:

1. **Context**: the bug summary from ensemble step 5.
2. **Reproducer info**: the reproducer file paths, the failing test output, and the test
   filter — so the agent understands what the test checks and how it fails.
3. **Build instructions**: since the agent's working directory is a worktree (not the
   original `$DNF5_SRC_DIR`), all build commands must override the source path:
   ```
   DNF5_SRC_DIR=$(pwd) dnf5-configure
   DNF5_SRC_DIR=$(pwd) dnf5-build
   DNF5_SRC_DIR=$(pwd) dnf5-test -R <test_filter>
   ```
   These are for reference only — agents should NOT run them.
4. **Task for the agent**:
   - Read the reproducer files and the relevant source code
   - Evaluate alternative fix approaches — consider correctness, scope, risk, maintainability
   - Implement the best fix (do NOT build or test — just write the code)
   - Report: chosen approach with reasoning, then full `git diff` output
   - As the very last step: `touch /tmp/fix-attempt-<SID>-<N>-done` (where `<SID>` is
     a session ID and `<N>` is the attempt number, 1-based)

Before spawning agents, generate a short random session ID and clean up any stale markers:

```bash
SID=$(head -c4 /dev/urandom | xxd -p)
rm -f /tmp/fix-attempt-*-done
```

Include the `SID` value in each agent's prompt so they use the same session ID.

**After spawning all agents: STOP.** Do not continue working, do not implement any fix
yourself, do not proceed to step 7. Ignore `<task-notification>` messages — they may
arrive before agents actually finish. Instead, poll for marker files:

```bash
ls /tmp/fix-attempt-<SID>-*-done 2>/dev/null | wc -l
```

Repeat every 30 seconds until the count equals N (the number of attempts). Only then
proceed to step 7.

## Ensemble step 7: Synthesize the best fix

After all marker files are present (all agents truly complete):

1. Review each agent's approach description and diff.
2. Compare them on correctness, scope, risk, and code quality.
3. Choose the best single approach, or combine the strongest elements from multiple
   approaches into a single fix.
4. Apply the chosen changes to the working tree (the original, not a worktree).
5. Clean up worktrees and marker files:
   ```bash
   git worktree prune
   rm -f /tmp/fix-attempt-*-done
   ```
   Then remove any leftover worktree directories and branches:
   ```bash
   git worktree list  # identify stale worktrees
   # for each stale worktree: git worktree remove <path>
   # for each stale branch: git branch -D <branch>
   ```
6. Build and confirm GREEN: `dnf5-build && dnf5-test -R <test_filter>`

Then continue with the standard steps 8–10 (regression check, commits, report).
In the report, note which attempt(s) contributed to the final fix and why.
