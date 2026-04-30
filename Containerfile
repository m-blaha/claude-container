FROM fedora:43

RUN dnf install -y nodejs git clang-tools-extra curl python3 pre-commit gh podman-remote && \
    dnf clean all && \
    ln -sf /usr/bin/podman-remote /usr/bin/podman

ARG CLAUDE_VERSION=2.1.83
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION}

WORKDIR /workspace

ENTRYPOINT ["claude"]
