#!/bin/bash
# GCE Startup Script for AI Tuber Body Node
# This script runs when the instance starts

set -e

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

get_metadata() {
  local key=$1
  local default=$2
  local value
  # Use -sf to fail silently/fast on 4xx/5xx errors
  value=$(curl -sf "http://metadata.google.internal/computeMetadata/v1/instance/attributes/${key}" -H "Metadata-Flavor: Google" || echo "")
  
  if [[ -n "$value" && ! "$value" =~ "<!DOCTYPE html>" ]]; then
    echo "$value"
  else
    echo "$default"
  fi
}

log "=== AI Tuber Body Node Startup Script Starting ==="

# Install Ops Agent
if ! systemctl is-active --quiet google-cloud-ops-agent; then
    log "Installing Ops Agent..."
    curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
    bash add-google-cloud-ops-agent-repo.sh --also-install
fi

# Configure Ops Agent for Docker logs
log "Configuring Ops Agent for Docker logs..."
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
    log "Installing Docker..."
    apt-get update -y
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    log "Docker installed successfully."
fi

# NOTE: docker compose plugin is pre-installed on DLVM. No need for standalone docker-compose.


# Configure Docker for Artifact Registry
log "Configuring Docker for Artifact Registry..."
ZONE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google" | cut -d/ -f4)
REGION=$(echo $ZONE | sed 's/-[a-z]$//')
PRIMARY_REGION=$(get_metadata "primary_region" "asia-northeast1")
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
gcloud auth configure-docker ${PRIMARY_REGION}-docker.pkg.dev --quiet

# NOTE: NVIDIA drivers, CUDA, and Docker NVIDIA runtime are pre-installed on the
# Deep Learning VM image (deeplearning-platform-release). No installation needed.
log "Skipping NVIDIA driver install (pre-installed in DLVM image)."

# Setup working directory
WORKDIR="/opt/ai-tuber"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Get Metadata with robust fetching
log "Fetching metadata resources..."
PROJECT_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
BUCKET_NAME=$(get_metadata "gcs_bucket" "")
CHARACTER_NAME=$(get_metadata "character_name" "ren")
REGISTRY="${PRIMARY_REGION}-docker.pkg.dev/${PROJECT_ID}/ai-tuber"

# Sync character assets and dictionary from GCS
if [[ -n "$BUCKET_NAME" && -n "$CHARACTER_NAME" ]]; then
    # Sync user dict (needed by VoiceVox)
    log "Syncing character dictionary from GCS..."
    mkdir -p "/opt/ai-tuber/data/mind/${CHARACTER_NAME}"
    gcloud storage cp "gs://${BUCKET_NAME}/mind/${CHARACTER_NAME}/user_dict.json" "/opt/ai-tuber/data/mind/${CHARACTER_NAME}/user_dict.json" || log "Warning: No dictionary found in GCS"

    # Fix permissions
    chmod -R 777 "/opt/ai-tuber/data"
else
    log "Skipping GCS sync: metadata BUCKET_NAME or CHARACTER_NAME is missing."
fi

# Create .env file for Docker Compose
log "Creating .env file from Secret Manager..."
# Check secret access before writing
GOOGLE_API_KEY=$(gcloud secrets versions access latest --secret="google-api-key" 2>/dev/null || echo "MISSING_KEY")
YT_SECRET=$(gcloud secrets versions access latest --secret="youtube-client-secret" 2>/dev/null || echo "{}")
YT_TOKEN=$(gcloud secrets versions access latest --secret="youtube-token" 2>/dev/null || echo "{}")

# Metadata-based stream config
STREAM_TITLE=$(get_metadata "stream_title" "紅月れんのAIニュース配信")
STREAM_DESC=$(get_metadata "stream_description" "Google ADKとGeminiを使用した次世代AITuberの配信テストです。")
STREAM_PRIVACY=$(get_metadata "stream_privacy" "private")

cat > .env << EOF
# Core Secrets
GOOGLE_API_KEY=${GOOGLE_API_KEY}
YOUTUBE_CLIENT_SECRET_JSON='${YT_SECRET}'
YOUTUBE_TOKEN_JSON='${YT_TOKEN}'

# Infrastructure Abstraction (SaaS-ready)
STORAGE_TYPE=gcs
SECRET_PROVIDER_TYPE=gcp
GCP_PROJECT_ID=${PROJECT_ID}
GCS_BUCKET_NAME=${BUCKET_NAME}

# Application States
CHARACTER_NAME=${CHARACTER_NAME}
STREAMING_MODE=true
STREAM_TITLE=${STREAM_TITLE}
STREAM_DESCRIPTION=${STREAM_DESC}
STREAM_PRIVACY=${STREAM_PRIVACY}
VOICEVOX_DATA_DIR=/opt/ai-tuber/data/mind/${CHARACTER_NAME}
EOF

# Create docker-compose.gce.yml dynamically
log "Generating docker-compose.gce.yml..."
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
    volumes:
      - \${VOICEVOX_DATA_DIR}:/home/user/.local/share/voicevox-engine-dev
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
      - STORAGE_TYPE=gcs
      - CHARACTER_NAME=${CHARACTER_NAME}
      - GCS_BUCKET_NAME=${BUCKET_NAME}
    shm_size: '2gb'
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu, video, graphics, utility]
EOF

# Pull images and start services
log "Starting AI Tuber services (pulling images quietly)..."
docker compose -f docker-compose.gce.yml pull --quiet || log "Warning: Image pull failed, attempting to start anyway..."

if ! docker compose -f docker-compose.gce.yml up -d; then
    log "ERROR: docker compose up failed. Recent container logs:"
    docker compose -f docker-compose.gce.yml logs --tail=50
    exit 1
fi

log "=== AI Tuber Body Node Started Successfully ==="
date
