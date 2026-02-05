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

# Install OpenTofu
RUN curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh \
    && chmod +x install-opentofu.sh \
    && ./install-opentofu.sh --install-method deb \
    && rm install-opentofu.sh

# Install Google Cloud SDK (Standalone)
RUN curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=/usr/local \
    && ln -s /usr/local/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud

# Install Python dependencies for both services to allow development in one container
COPY src/saint_graph/requirements.txt /tmp/sg-req.txt
COPY src/body/cli/requirements.txt /tmp/body-req.txt
COPY requirements-dev.txt /tmp/dev-req.txt
RUN pip install -r /tmp/sg-req.txt && \
    pip install -r /tmp/body-req.txt && \
    pip install -r /tmp/dev-req.txt

# Set the default shell to bash rather than sh
ENV SHELL /bin/bash
