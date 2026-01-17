FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install basic packages, OBS PPA, and OBS Studio
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:obsproject/obs-studio \
    && apt-get update && apt-get install -y \
    obs-studio \
    xvfb \
    fluxbox \
    x11vnc \
    novnc \
    websockify \
    supervisor \
    pulseaudio \
    libegl1-mesa \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    dbus-x11 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create directories and pre-configure OBS WebSocket
RUN mkdir -p /var/run/supervisor /var/log/supervisor /root/.config/obs-studio/plugin_config/obs-websocket \
    && echo '{"address": "0.0.0.0", "port": 4455, "enabled": true, "authentication_enabled": false, "server_enabled": true, "server_port": 4455, "auth_required": false, "first_load": false}' > /root/.config/obs-studio/plugin_config/obs-websocket/config.json

# Copy configuration files
COPY docker/obs/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/obs/apps /root/.fluxbox/apps

# Expose ports
# 8080: noVNC web interface
# 4455: OBS WebSocket
EXPOSE 8080 4455

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
