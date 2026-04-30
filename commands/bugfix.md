---
description: Test-driven bugfix workflow for dnf5 using the dev container
---

You have access to a Fedora dev container with all dnf5 build dependencies.
`dnf5-configure`, `dnf5-build`, `dnf5-test`, `dnf5-exec` are bash commands on your PATH.

Follow this red-green-refactor workflow strictly. Do not skip steps.

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

### Option B: Ad-hoc reproducer with built binary

When the bug requires a full dnf5 invocation (transaction handling, CLI behavior,
repo interaction, etc.):

1. Create test packages in the dev container:

```bash
dnf5-exec bash -c 'mkdir -p /tmp/repro/specs'
```

Write spec files, then build:

```bash
dnf5-exec rpmbuild --define "_topdir /tmp/repro/build" -bb /tmp/repro/specs/pkg.spec
dnf5-exec createrepo_c /tmp/repro/build/RPMS/
```

2. Run the built dnf5 binary against the crafted repo:

```bash
dnf5-exec $DNF5_SRC_DIR/build-dev/dnf5/dnf5 \
    --installroot=/tmp/repro/root \
    --repofrompath=testrepo,/tmp/repro/build/RPMS \
    --disablerepo='*' --enablerepo=testrepo \
    install problematic-package
```

3. Verify the bug is reproduced in the output.

## Step 3: Confirm the test fails (RED)

Run the reproducer and confirm it demonstrates the broken behavior.
If the test passes, the reproducer doesn't capture the bug — revise it.

```bash
dnf5-build
dnf5-test -R test_bugname
```

Report: "Test fails as expected: [describe the failure]"

## Step 4: Fix the bug

Now fix the code. Keep the change minimal — fix only the bug, don't refactor.

## Step 5: Confirm the test passes (GREEN)

```bash
dnf5-build
dnf5-test -R test_bugname
```

If it still fails, iterate on the fix. Do not proceed until the test passes.

Report: "Test passes after fix."

## Step 6: Run full test suite (regression check)

```bash
dnf5-test
```

If any other tests fail, investigate whether the fix caused a regression.
Fix regressions before reporting success.

## Step 7: Create commits

Create a logical set of commits. The structure depends on the reproducer approach:

**If Option A was used (unit test in dnf5 repo):**
1. Test commit: spec files (if any) + test case
2. Fix commit: the code change

**If Option B was used (ad-hoc reproducer):**
1. Fix commit only — include reproduction steps in the commit message body so reviewers
   can verify the fix. Do not commit ad-hoc test files into the dnf5 repo (behavioral
   tests belong in ci-dnf-stack).

If the fix touches multiple independent areas, split into separate commits per area.

Commit message format — follow the project's existing style from `git log`. Typically:
- First line: short summary (imperative mood)
- Blank line, then body explaining the root cause and what the fix changes
- Reference the bug/issue if applicable

## Step 8: Report

Summarize:
- Root cause of the bug
- What the fix changes
- How the bug was reproduced
- Full test suite result
- Commits created
