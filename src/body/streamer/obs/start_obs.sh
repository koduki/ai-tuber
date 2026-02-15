#!/bin/bash
# Clean up OBS lock files from previous runs
rm -f /root/.config/obs-studio/basic/scenes/*.lock
rm -f /root/.config/obs-studio/basic/profiles/*/*.lock
rm -f /root/.config/obs-studio/global.ini.lock
rm -f /root/.config/obs-studio/plugin_config/obs-websocket/.obs_websocket_lock

# Wait for assets to be downloaded
ASSETS_DIR="${ASSETS_DIR:-/app/assets}"
MARKER="$ASSETS_DIR/.assets_ready"
echo "Waiting for assets to be ready..."
WAIT_COUNT=0
while [ ! -f "$MARKER" ]; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ $WAIT_COUNT -ge 120 ]; then
        echo "ERROR: Assets not ready after 120s. Exiting."
        exit 1
    fi
done
echo "Assets ready (waited ${WAIT_COUNT}s). Starting OBS..."

# Set platform for headless
export QT_QPA_PLATFORM=xcb

# Start OBS Studio with Safe Mode disabled
# We don't use --verbose here to keep logs cleaner, but keeping it for debugging if needed
exec obs --disable-shutdown-check --verbose 2>&1

