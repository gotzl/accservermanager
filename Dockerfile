FROM python:3.7.4-alpine3.10

RUN apk add --no-cache shadow wine freetype ncurses-libs && \
    ln -s /usr/bin/wine64 /usr/bin/wine && \
    rm -rf /var/cache/apk/*

RUN mkdir -p /accservermanager /data

WORKDIR /accservermanager

RUN useradd -ms /bin/bash someuser && \
    chown -R someuser:someuser /accservermanager /data

USER someuser
VOLUME /data

COPY ./requirements.txt .
RUN pip3 install --user --no-cache-dir -r requirements.txt

ENV WINEARCH=win64 \
    WINEDEBUG=-all
RUN wineboot --init

COPY . /accservermanager

EXPOSE 9231/udp 9232/tcp 8000/tcp
CMD ["python3", "manage.py", "runserver", "--insecure", "0.0.0.0:8000"]
