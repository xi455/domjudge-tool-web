ARG PYTHON_VERSION=3.8.13
FROM python:${PYTHON_VERSION} as base

RUN pip install poetry

COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock

RUN poetry export --format=requirements.txt --output=requirements.txt --without-hashes \
    && pip install -r requirements.txt \
    && rm -rf /var/lib/{apt,dpkg,cache,log}

# App
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      libpq-dev \
      cron \
      libxml2 \
      && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=base /usr/local/lib/ /usr/local/lib/
COPY --from=base /usr/local/bin/ /usr/local/bin/

VOLUME /app/log
VOLUME /app/media
VOLUME /app/assets

EXPOSE 8000

COPY ./docker /docker
COPY /docker/django-logrotate /etc/cron.d/django-logrotate
Run crontab /etc/cron.d/django-logrotate

RUN \
  mv -v /docker/entrypoint.sh /usr/local/bin/entrypoint && \
  chmod +x /usr/local/bin/entrypoint && \
  \
  mv -v /docker/django.logrotate.conf /etc/logrotate.d/django && \
  chmod 644 /etc/logrotate.d/django && \
  \
  mv -v /docker/wait_database.py . && \
  \
  rm -rvf /docker

COPY ./src .

CMD [ "entrypoint" ]
