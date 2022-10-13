FROM python:3.8.13-alpine

WORKDIR /app

VOLUME /app/log
VOLUME /app/media
VOLUME /app/assets

EXPOSE 8000

ENV POETRY_VIRTUALENVS_CREATE=false

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN \
  apk add --update --no-cache --virtual build-deps \
    build-base linux-headers libc-dev \
    pcre-dev git openssl-dev cargo && \
  \
  apk add --no-cache \
    libuuid pcre mailcap logrotate \
    musl-dev libxslt-dev libffi-dev \
    jpeg-dev zlib-dev postgresql-dev && \
  \
  pip3 install --no-cache-dir poetry && \
  poetry install --only main && \
  \
  apk del build-deps && \
  rm -rf ~/.cache

COPY ./docker /docker

RUN \
  mv -v /docker/entrypoint.sh /usr/local/bin/entrypoint && \
  chmod +x /usr/local/bin/entrypoint && \
  \
  mv -v /docker/django.logrotate.conf /etc/logrotate.d/django && \
  mv -v /docker/django-logrotate.sh /etc/periodic/daily/django-logrotate && \
  chmod 644 /etc/logrotate.d/django && \
  chmod +x /etc/periodic/daily/django-logrotate && \
  \
  mv -v /docker/wait_database.py . && \
  \
  rm -rvf /docker

COPY ./src .

CMD [ "entrypoint" ]
