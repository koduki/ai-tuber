#!/bin/sh

# SET Virtual Audio Device
#pulseaudio -D --exit-idle-time=-1 --system
#pactl load-module module-null-sink sink_name=SpeakerOutput sink_properties=device.description="Dummy_Output"
#pacmd load-module module-virtual-source source_name=VirtualMicrophone
pulseaudio -D --exit-idle-time=-1 
pactl load-module module-null-sink sink_name=SpeakerOutput sink_properties=device.description="Dummy_Output"

## Setup OBS Config
python3 /root/init-yt-key.py

## Run VNC & OBS
vncserver -localhost :1
DISPLAY=:1 obs &
websockify --web=/usr/share/novnc 6080 localhost:5901