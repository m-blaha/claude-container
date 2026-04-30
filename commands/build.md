---
description: Configure, build, and test the dnf5 project in the dev container
---

You have access to a Fedora dev container with all dnf5 build dependencies.
Run these as bash commands — they are executable scripts on your PATH.

## Steps

### 1. Check dev container is available

```bash
echo "$DNF5_DEV_CONTAINER"
```

If empty, tell the user the dev container is not running. They need to start `pclaude`
from a directory under `~/src/dnf5/`.

### 2. Configure (if needed)

Check if cmake has already been configured:

```bash
ls "$DNF5_SRC_DIR/build-dev/CMakeCache.txt" 2>/dev/null
```

If not, run:

```bash
dnf5-configure
```

### 3. Build

```bash
dnf5-build
```

If the build fails, analyze the errors and suggest fixes. Do not proceed to tests.

### 4. Test

```bash
dnf5-test
```

To run a specific test:

```bash
dnf5-test -R <test_name>
```

Report results. If tests fail, analyze the output and suggest fixes.

## Other commands

```bash
# Build a specific make target
dnf5-build <target>

# Pass extra cmake flags
dnf5-configure -DWITH_PYTHON3=OFF

# Run any command in the dev container
dnf5-exec <command> [args...]
```
