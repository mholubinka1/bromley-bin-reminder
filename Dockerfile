FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV UV_FROZEN=1
ENV UV_NO_CACHE=1

RUN useradd -ms /bin/bash sel_user

RUN apt-get update && apt-get install -y wget firefox-esr xvfb

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux-aarch64.tar.gz
RUN tar -xzvf geckodriver-v0.33.0-linux-aarch64.tar.gz -C /usr/local/bin
RUN chmod +x /usr/local/bin/geckodriver

WORKDIR /app
RUN mkdir -p config
VOLUME /config

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

USER sel_user

COPY app ./app
ENV ENV_FLAG="docker"

CMD [ "uv", "run", "--no-sync", "python", "./app/main.py", "--config-file", "/config/config.yml"]
