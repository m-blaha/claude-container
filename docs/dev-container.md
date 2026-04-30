# Dev Container for dnf5

When `pclaude` is run from a directory under `~/src/dnf5/`, it automatically starts a
Fedora-based dev container with all build dependencies pre-installed alongside the Claude
container. Both containers share the source tree at the same absolute path.

## Prerequisites

Enable the Podman user socket on the host:

```bash
systemctl --user enable --now podman.socket
```

## Commands

These commands are available inside the Claude session:

```bash
# Configure (first time, or after CMakeLists.txt changes)
dnf5-configure

# Build (incremental)
dnf5-build

# Build a specific target
dnf5-build test_libdnf5

# Run all tests
dnf5-test

# Run a specific test by name
dnf5-test -R test_libdnf5_rpm

# Verbose test output
dnf5-test -V

# Pass extra cmake options
dnf5-configure -DWITH_PYTHON3=OFF

# Run any command in the dev container
dnf5-exec rpm --version
```

## How It Works

- `pclaude` detects the dnf5 worktree from `$PWD` and sets `DNF5_SRC_DIR`
- A dev container (`dnf5-dev-<pid>`) starts with `sleep infinity`, sharing `~/src`
- The host's Podman socket is mounted into Claude's container at `/run/podman.sock`
- Wrapper scripts in `dev-scripts/` use `podman exec` via the socket to run commands
  in the dev container
- The build directory is `build-dev/` inside the worktree (gitignored)
- The dev container is stopped automatically when the Claude session ends

## Dev Container Image

Based on `ghcr.io/rpm-software-management/dnf-ci-host` (the project's CI image), which
includes all ~40 BuildRequires packages from `dnf5.spec`. Rebuilt weekly by `pclaude`.

Image definition: `Containerfile.dnf5-dev`

## Architecture

```
pclaude (host)
  |
  +-- dnf5-dev-<pid>  (Fedora, all build deps, sleep infinity)
  |     ^
  |     | podman exec via /run/podman.sock
  |     |
  +-- claude-code     (Node, Claude CLI)
        |-- dnf5-build, dnf5-test, etc. (wrapper scripts)
        |-- ~/src (shared bind mount, same paths)
```
