#!/bin/bash
# GCE Startup Script for AI Tuber Body Node
# This script runs when the instance starts

set -e

echo "=== AI Tuber Body Node Startup Script ==="
date

# Install Ops Agent
echo "Installing Ops Agent..."
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
bash add-google-cloud-ops-agent-repo.sh --also-install

# Configure Ops Agent for Docker logs
echo "Configuring Ops Agent for Docker logs..."
cat > /etc/google-cloud-ops-agent/config.yaml << EOF
logging:
  receivers:
    docker_logs:
      type: files
      include_paths:
        - /var/lib/docker/containers/*/*.log
  service:
    pipelines:
      docker_pipeline:
        receivers:
          - docker_logs
EOF
systemctl restart google-cloud-ops-agent

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    # Add Docker's official GPG key:
    apt-get update
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update

    # Install the Docker packages.
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="v2.24.0"
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Configure Docker for Artifact Registry
echo "Configuring Docker for Artifact Registry..."
# Note: This requires the GCE instance to have the correct region
REGION=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google" | cut -d/ -f4 | sed 's/-[a-z]$//')
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Install NVIDIA GPU drivers if not present
if ! nvidia-smi &> /dev/null; then
    echo "Installing NVIDIA GPU drivers using GCP's official method..."
    
    # Use GCP's recommended GPU driver installer
    # This handles kernel compatibility automatically
    curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output install_gpu_driver.py
    python3 install_gpu_driver.py
    
    echo "NVIDIA drivers installed successfully."
fi

# Install NVIDIA Docker runtime if not present
if ! dpkg -l | grep -q nvidia-docker2; then
    echo "Installing NVIDIA Docker runtime..."
    
    # Add NVIDIA GPG key and repository
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    # Install
    apt-get update
    apt-get install -y nvidia-docker2
    systemctl restart docker
fi

# Setup working directory
WORKDIR="/opt/ai-tuber"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Get Metadata
PROJECT_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
REGION=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google" | cut -d/ -f4 | sed 's/-[a-z]$//')
BUCKET_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs_bucket" -H "Metadata-Flavor: Google")
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-tuber"

# Create .env file for Docker Compose
echo "Creating .env file..."
cat > .env << EOF
GOOGLE_API_KEY=$(gcloud secrets versions access latest --secret="google-api-key")
YOUTUBE_CLIENT_SECRET_JSON='$(gcloud secrets versions access latest --secret="youtube-client-secret")'
YOUTUBE_TOKEN_JSON='$(gcloud secrets versions access latest --secret="youtube-token")'
GCS_BUCKET_NAME=${BUCKET_NAME}
STREAMING_MODE=true
STREAM_TITLE="紅月れんのAIニュース配信テスト"
STREAM_DESCRIPTION="Google ADKとGeminiを使った次世代AITuber、紅月れんのニュース配信テストです。"
STREAM_PRIVACY=private
EOF

# Create docker-compose.gce.yml dynamically
echo "Creating docker-compose.gce.yml..."
cat > docker-compose.gce.yml << EOF
volumes:
  voice_share:

services:
  body-streamer:
    image: ${REGISTRY}/body-streamer:latest
    ports:
      - "8000:8000"
    stdin_open: true
    tty: true
    volumes:
      - voice_share:/app/shared/voice
    env_file: .env
    environment:
      - PORT=8000
      - VOICEVOX_HOST=voicevox
      - VOICEVOX_PORT=50021
      - OBS_HOST=obs-studio
      - OBS_PORT=4455
    depends_on:
      voicevox:
        condition: service_healthy
      obs-studio:
        condition: service_started
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://localhost:8000/health" ]
      interval: 5s
      timeout: 2s
      retries: 5

  voicevox:
    image: voicevox/voicevox_engine:nvidia-ubuntu20.04-latest
    ports:
      - "50021:50021"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: [ "CMD", "wget", "--no-verbose", "--tries=1", "--output-document=/dev/null", "http://localhost:50021/version" ]
      interval: 10s
      timeout: 5s
      retries: 5

  obs-studio:
    image: ${REGISTRY}/obs-studio:latest
    ports:
      - "8080:8080"
      - "4455:4455"
    volumes:
      - voice_share:/app/shared/voice
    environment:
      - DISPLAY=:99
    shm_size: '2gb'
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu, video, graphics, utility, display]
EOF

# Pull images and start services
echo "Starting AI Tuber services..."
docker-compose -f docker-compose.gce.yml pull
docker-compose -f docker-compose.gce.yml up -d

echo "=== AI Tuber Body Node started successfully ==="
date
