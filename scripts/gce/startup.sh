#!/bin/bash
# GCE Startup Script for AI Tuber Body Node
# This script runs when the instance starts

set -e

echo "=== AI Tuber Body Node Startup Script ==="
date

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="2.24.0"
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
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

# Clone or update the repository
REPO_DIR="/opt/ai-tuber"
REPO_URL="https://github.com/YOUR_USERNAME/ai-tuber.git"  # Update with your repo

if [ -d "$REPO_DIR" ]; then
    echo "Updating repository..."
    cd "$REPO_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Download .env from GCS Metadata
echo "Setting up environment variables..."
BUCKET_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs_bucket" -H "Metadata-Flavor: Google")

# Create .env file from environment variables or Secret Manager
cat > "$REPO_DIR/.env" << EOF
GOOGLE_API_KEY=$(gcloud secrets versions access latest --secret="google-api-key")
GCS_BUCKET_NAME=${BUCKET_NAME}
STREAMING_MODE=true
STREAM_PRIVACY=public
EOF

# Pull latest Docker images
echo "Pulling Docker images..."
cd "$REPO_DIR"
docker-compose -f docker-compose.gce.yml pull

# Start services (GCE specific compose file)
echo "Starting AI Tuber services..."
docker-compose -f docker-compose.gce.yml up -d

echo "=== AI Tuber Body Node started successfully ==="
date
