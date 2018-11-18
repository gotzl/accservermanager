FROM ubuntu:latest

ENV WINEARCH=win64
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y xvfb cabextract wget gnupg software-properties-common python3-pip && \
    wget -nc https://dl.winehq.org/wine-builds/Release.key && \
    apt-key add Release.key && \
    apt-add-repository https://dl.winehq.org/wine-builds/ubuntu/ && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --install-recommends winehq-stable && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install django django-material random-word

ADD . /accservermanager
WORKDIR /accservermanager

RUN useradd -ms /bin/bash someuser
RUN chown -R someuser:someuser /accservermanager
USER someuser

EXPOSE 9231 9232 8000
VOLUME /server

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
