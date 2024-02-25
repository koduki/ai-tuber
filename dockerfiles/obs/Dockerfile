FROM debian:12-slim

RUN apt-get -y update \
    && apt install -y task-xfce-desktop xfonts-base xfonts-75dpi xfonts-100dpi xfonts-scalable \
    && apt install -y websockify novnc tightvncserver \
    && apt install -y obs-studio