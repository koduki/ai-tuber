#!/bin/bash
# Clean up OBS lock files from previous runs
rm -f /root/.config/obs-studio/basic/scenes/*.lock
rm -f /root/.config/obs-studio/basic/profiles/*/*.lock
rm -f /root/.config/obs-studio/global.ini.lock
rm -f /root/.config/obs-studio/plugin_config/obs-websocket/.obs_websocket_lock

# Start OBS Studio with Safe Mode disabled and verbose logging
exec obs --disable-shutdown-check --verbose 2>&1
