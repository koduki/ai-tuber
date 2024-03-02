FROM debian:12-slim

RUN apt-get -y update \
    && apt install -y xfonts-base xfonts-75dpi xfonts-100dpi xfonts-scalable \
    && apt install -y websockify novnc tightvncserver \
    && apt install -y obs-studio

RUN apt install -y fluxbox 

ENV USER=root
ADD ./resources/config /root/.config
ADD ./resources/vnc /root/.vnc
ADD ./resources/startup.sh /root/startup.sh

RUN chmod a+x /root/startup.sh
RUN echo foobar | vncpasswd -f > /root/.vnc/passwd
RUN chmod 600 /root/.vnc/passwd

CMD ["/root/startup.sh"]