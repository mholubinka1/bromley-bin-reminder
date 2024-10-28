FROM python:3.11.0-alpine3.17

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

RUN apk add --no-cache --virtual .deps g++ gcc musl-dev python3-dev libffi-dev openssl-dev cargo pkgconfig
RUN apk add libpq-dev
#RUN apk add chromium-chromedriver

RUN python3 -m venv ${POETRY_VENV} \
    && ${POETRY_VENV}/bin/pip install --upgrade pip setuptools wheel

ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN ${POETRY_VENV}/bin/pip install poetry
RUN poetry install --no-root --only main

RUN apk del .deps

COPY app ./app

USER 999

CMD [ "poetry", "run", "python", "./app/main.py"]