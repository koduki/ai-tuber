# FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04
FROM debian:12-slim

ENV YT_LIVE_KEY=
EXPOSE 6080

# Set Timezone
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# INSTALL OBS with GUI
RUN apt-get -y update && apt install -y \
    websockify novnc tightvncserver \
    fluxbox
RUN apt install -y obs-studio

# INSTALL others
RUN apt install -y \ 
    python3-pip \
    curl

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# ADD RESOURCES
ENV USER=root
RUN echo 'no cache'
ADD ./dockerfiles/config /root/.config
ADD ./dockerfiles/vnc /root/.vnc
ADD ./dockerfiles/fluxbox /root/.fluxbox
ADD ./dockerfiles/start-vnc_obs.sh /root/start-vnc_obs.sh
ADD ./dockerfiles/init-yt-key.py /root/init-yt-key.py
ADD ./dockerfiles/bgm.mp3 /root/

# CRLF to LF
RUN sed -i 's/\r$//' /root/start-vnc_obs.sh && \
    sed -i 's/\r$//' /root/init-yt-key.py && \
    sed -i 's/\r$//' /root/.fluxbox/apps && \
    sed -i 's/\r$//' /root/.vnc/xstartup

# SET VNC PASSWORD
RUN echo vnc | vncpasswd -f > /root/.vnc/passwd
RUN chmod 600 /root/.vnc/passwd

# Install App
ADD ./ /workspaces/ai-tuber
RUN cd /workspaces/ai-tuber && poetry install

# START
WORKDIR /root
RUN chmod a+x /root/start-vnc_obs.sh
ENTRYPOINT ["/root/start-vnc_obs.sh"]