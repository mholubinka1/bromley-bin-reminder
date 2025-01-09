FROM python:3.11-slim

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

RUN useradd -ms /bin/bash sel_user

RUN apt-get update && apt-get install -y wget firefox-esr xvfb

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux-aarch64.tar.gz
RUN tar -xzvf geckodriver-v0.33.0-linux-aarch64.tar.gz -C /usr/local/bin
RUN chmod +x /usr/local/bin/geckodriver

RUN python3 -m venv ${POETRY_VENV} \
    && ${POETRY_VENV}/bin/pip install --upgrade pip setuptools wheel

ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app
RUN mkdir -p config
VOLUME /config

COPY pyproject.toml poetry.lock ./

RUN ${POETRY_VENV}/bin/pip install poetry
RUN poetry install --no-root --only main
 
USER sel_user

COPY app ./app
ENV ENV_FLAG="docker"

CMD [ "poetry", "run", "python", "./app/main.py", "--config-file", "/config/config.yml"]