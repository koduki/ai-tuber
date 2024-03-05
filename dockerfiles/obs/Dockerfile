FROM debian:12-slim

ENV YT_LIVE_KEY=
EXPOSE 6080

# INSTALL
RUN apt-get -y update && apt install -y \
    websockify novnc tightvncserver \
    fluxbox
RUN apt install -y obs-studio
RUN apt install -y \ 
    python3-pip \
    curl

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# ADD RESOURCES
ENV USER=root
ADD ./resources/config /root/.config
ADD ./resources/vnc /root/.vnc
ADD ./resources/start-vnc_obs.sh /root/start-vnc_obs.sh
ADD ./resources/init-yt-key.py /root/init-yt-key.py
ADD ./resources/bgm.mp3 /root/

# SET VNC PASSWORD
RUN echo foobar | vncpasswd -f > /root/.vnc/passwd
RUN chmod 600 /root/.vnc/passwd

# Install App
ADD ./app /app
RUN cd /app && poetry install

# START
WORKDIR /root
RUN chmod a+x /root/start-vnc_obs.sh
CMD ["/root/start-vnc_obs.sh"]