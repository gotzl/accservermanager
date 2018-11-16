FROM ubuntu:latest

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y xvfb cabextract wget gnupg software-properties-common && \
    wget -nc https://dl.winehq.org/wine-builds/Release.key && \
    apt-key add Release.key && \
    apt-add-repository https://dl.winehq.org/wine-builds/ubuntu/ && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --install-recommends winehq-stable && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y python3-pip && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install django django-material

RUN useradd -ms /bin/bash wineuser
USER wineuser
WORKDIR /home/wineuser

ENV WINEARCH=win64
#RUN wget https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks && \
#    chmod +x winetricks && \
#    wine wineboot --init && \
#    xvfb-run -a ./winetricks -q vcrun2015

ADD server /server
WORKDIR /server

EXPOSE 9231 9232 8000

ADD accservermanager /accservermanager
WORKDIR /accservermanager

USER root
RUN chown -R wineuser:wineuser /accservermanager /server
USER wineuser

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
