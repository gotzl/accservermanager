FROM ubuntu:latest

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y wine-development python3-pip && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /accservermanager /data

WORKDIR /accservermanager

RUN useradd -ms /bin/bash someuser && \
        chown -R someuser:someuser /accservermanager /data

USER someuser
VOLUME /data

ADD requirements.txt .
RUN pip3 install --user --no-cache-dir -r requirements.txt

ENV WINEARCH=win64 \
    WINEDEBUG=-all
RUN wineboot --init

ADD . /accservermanager

EXPOSE 9231 9232 8000
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
