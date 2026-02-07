FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Preemptively remove Yarn's apt list to avoid GPG errors during initial apt-get update
RUN rm -f /etc/apt/sources.list.d/yarn.list

# Debug: List apt sources and contents before update
RUN ls -la /etc/apt/sources.list.d/ \
    && cat /etc/apt/sources.list \
    && cat /etc/apt/sources.list.d/*.list || true \
    && grep -r yarn /etc/apt/ || true

# Install wget/git-lfs which is required by VSCode server install/LFS
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget git-lfs ca-certificates curl gnupg socat procps iproute2 lsb-release \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    \
    # Add Yarn GPG key and repository
    && curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor | tee /etc/apt/keyrings/yarn-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/yarn-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/yarn-archive-keyring.gpg] https://dl.yarnpkg.com/debian stable main" > /etc/apt/sources.list.d/yarn.list \
    \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Install OpenTofu
RUN curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh \
    && chmod +x install-opentofu.sh \
    && ./install-opentofu.sh --install-method deb \
    && rm install-opentofu.sh

# Install Google Cloud SDK (APT)
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update && apt-get install -y google-cloud-cli

# Install Python dependencies for both services to allow development in one container
COPY src/saint_graph/requirements.txt /tmp/sg-req.txt
COPY src/body/cli/requirements.txt /tmp/body-req.txt
COPY requirements-dev.txt /tmp/dev-req.txt
RUN pip install -r /tmp/sg-req.txt && \
    pip install -r /tmp/body-req.txt && \
    pip install -r /tmp/dev-req.txt

# Set the default shell to bash rather than sh
ENV SHELL /bin/bash
