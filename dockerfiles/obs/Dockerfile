FROM debian:12-slim

# INSTALL
RUN apt-get -y update && apt install -y obs-studio -o Acquire::http::Timeout=30 -o Acquire::Retries=3
RUN apt install -y \
    websockify novnc tightvncserver \
    fluxbox \
    python3-pip
RUN /bin/sh -c pip install \
    obsws-python

# ADD RESOURCES
ENV USER=root
ADD ./resources/config /root/.config
ADD ./resources/vnc /root/.vnc
ADD ./resources/start-vnc_obs.sh /root/start-vnc_obs.sh
ADD ./resources/init-yt-key.py /root/init-yt-key.py
ADD ./resources/start-yt-live.py /root/start-yt-live.py

# SET VNC PASSWORD
RUN echo foobar | vncpasswd -f > /root/.vnc/passwd
RUN chmod 600 /root/.vnc/passwd

# START
RUN chmod a+x /root/start-vnc_obs.sh
CMD ["/root/start-vnc_obs.sh"]