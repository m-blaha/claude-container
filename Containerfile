FROM node:22-slim

RUN apt-get update && apt-get install -y git clangd curl python3 pre-commit && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

ARG CLAUDE_VERSION=2.1.83
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION}

WORKDIR /workspace

ENTRYPOINT ["claude"]
