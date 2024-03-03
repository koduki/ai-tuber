#!/bin/sh

## Setup Config
python3 /root/init-yt-key.py

## Run VNC & OBS
vncserver -localhost :1
DISPLAY=:1 obs &
websockify --web=/usr/share/novnc 6080 localhost:5901