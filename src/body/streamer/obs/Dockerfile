FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all,graphics,utility,video,display

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
    libglvnd0 \
    libglx0 \
    dbus-x11 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create directories and pre-configure OBS
RUN mkdir -p /var/run/supervisor /var/log/supervisor \
    /root/.config/obs-studio/plugin_config/obs-websocket \
    /root/.config/obs-studio/basic/profiles/Untitled \
    /root/.config/obs-studio/basic/scenes \
    && echo '{"address": "0.0.0.0", "port": 4455, "enabled": true, "authentication_enabled": false, "server_enabled": true, "server_port": 4455, "auth_required": false, "first_load": false}' > /root/.config/obs-studio/plugin_config/obs-websocket/config.json

# Copy configuration files
COPY src/body/streamer/obs/config/fluxbox/init /root/.fluxbox/init
COPY src/body/streamer/obs/config/global.ini /root/.config/obs-studio/global.ini
COPY src/body/streamer/obs/config/basic/profiles/Untitled/basic.ini /root/.config/obs-studio/basic/profiles/Untitled/basic.ini
COPY src/body/streamer/obs/config/basic/scenes/Untitled.json /root/.config/obs-studio/basic/scenes/Untitled.json
COPY src/body/streamer/obs/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY src/body/streamer/obs/apps /root/.fluxbox/apps
COPY src/body/streamer/obs/start_obs.sh /usr/local/bin/start_obs.sh
RUN chmod +x /usr/local/bin/start_obs.sh

# Copy character assets
COPY data/mind/ren/assets /app/assets

# Expose ports
# 8080: noVNC web interface
# 4455: OBS WebSocket
EXPOSE 8080 4455

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
