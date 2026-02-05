#!/bin/bash
# GCE Shutdown Script for AI Tuber Body Node
# This script runs before the instance stops

set -e

echo "=== AI Tuber Body Node Shutdown Script ==="
date

REPO_DIR="/opt/ai-tuber"

if [ -d "$REPO_DIR" ]; then
    echo "Stopping AI Tuber services..."
    cd "$REPO_DIR"
    docker-compose -f docker-compose.gce.yml down
    
    echo "Services stopped successfully"
else
    echo "Repository directory not found, nothing to stop"
fi

echo "=== AI Tuber Body Node shutdown complete ==="
date
