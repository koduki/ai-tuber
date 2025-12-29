FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Install wget/git-lfs which is required by VSCode server install/LFS
RUN apt-get update && apt-get install -y wget git-lfs ca-certificates curl gnupg && git lfs install



# Install GitHub CLI
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y gh

# Install Python dependencies for both services to allow development in one container
RUN pip install google-genai httpx google-adk fastapi uvicorn sse-starlette

# Set the default shell to bash rather than sh
ENV SHELL /bin/bash
