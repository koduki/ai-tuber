#!/bin/bash
# Clean up OBS lock files from previous runs
rm -f /root/.config/obs-studio/basic/scenes/*.lock
rm -f /root/.config/obs-studio/basic/profiles/*/*.lock
rm -f /root/.config/obs-studio/global.ini.lock
rm -f /root/.config/obs-studio/plugin_config/obs-websocket/.obs_websocket_lock

# Set platform for headless
export QT_QPA_PLATFORM=xcb

# Start OBS Studio with Safe Mode disabled
# We don't use --verbose here to keep logs cleaner, but keeping it for debugging if needed
exec obs --disable-shutdown-check --verbose 2>&1
