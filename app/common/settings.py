import logging.config
from dataclasses import dataclass
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

DEFAULT_DAILY_POLL_TIME = "18:00"
DEFAULT_TZ = "Europe/London"
DEFAULT_NTFY_SERVER = "https://ntfy.sh"


def is_null_or_empty(s: str | None) -> bool:
    if not s:
        return True
    return s.strip() == ""


@dataclass
class RemindSettings:
    target_emails: list[str]
    time: str
    tz: str


@dataclass
class SMTPSettings:
    username: str
    password: str | None
    server: str
    port: int


@dataclass
class NtfySettings:
    server: str
    topic: str


def _build_ntfy_settings(ntfy_yaml: dict[str, Any] | None) -> NtfySettings | None:
    if not ntfy_yaml:
        return None
    topic = str(ntfy_yaml.get("topic") or "").strip()
    if is_null_or_empty(topic):
        return None
    server = str(ntfy_yaml.get("server") or "").strip()
    return NtfySettings(
        server=DEFAULT_NTFY_SERVER if is_null_or_empty(server) else server,
        topic=topic,
    )


@dataclass
class ApplicationSettings:
    wasteworks_url: str
    remind: RemindSettings
    smtp: SMTPSettings
    ntfy: NtfySettings | None
    timezone: ZoneInfo


def _resolve_timezone(name: str) -> ZoneInfo | None:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return None


def _poll_time(raw_time: str) -> str:
    if is_null_or_empty(raw_time):
        logger.warning(
            f"Custom daily poll time not provided, using default: {DEFAULT_DAILY_POLL_TIME}"
        )
        return DEFAULT_DAILY_POLL_TIME
    return raw_time


def _timezone(raw_name: str) -> tuple[str, ZoneInfo]:
    if is_null_or_empty(raw_name):
        logger.warning(f"Custom timezone not provided, using default: {DEFAULT_TZ}")
        return DEFAULT_TZ, ZoneInfo(DEFAULT_TZ)
    resolved = _resolve_timezone(raw_name)
    if resolved is None:
        logger.warning(f"Unrecognised timezone {raw_name}, using default: {DEFAULT_TZ}")
        return DEFAULT_TZ, ZoneInfo(DEFAULT_TZ)
    return raw_name, resolved


def parse_settings(raw: dict[str, Any]) -> ApplicationSettings:
    remind = raw["remind"]
    smtp = raw["smtp"]
    wasteworks_url = remind["url"]
    target_emails = remind["email_addresses"]
    if is_null_or_empty(wasteworks_url):
        raise RuntimeError("A valid wasteworks URL must be provided.")
    poll_time = _poll_time(remind["time"])
    tz_name, timezone = _timezone(remind.get("tz", ""))
    if is_null_or_empty(smtp["username"]):
        raise RuntimeError("A valid sender e-mail address must be provided.")
    if is_null_or_empty(smtp["server"]) or smtp["port"] is None:
        raise RuntimeError("SMTP server and port configurations must be provided.")
    return ApplicationSettings(
        wasteworks_url=wasteworks_url,
        remind=RemindSettings(target_emails=target_emails, time=poll_time, tz=tz_name),
        smtp=SMTPSettings(
            username=smtp["username"],
            password=smtp["password"],
            server=smtp["server"],
            port=smtp["port"],
        ),
        ntfy=_build_ntfy_settings(raw.get("ntfy")),
        timezone=timezone,
    )


def load_settings(path: str) -> ApplicationSettings:
    try:
        with open(path, "r") as file:
            raw = yaml.safe_load(file)
        logger.info(f"Successfully loaded settings from {path}")
        return parse_settings(raw)
    except Exception as error:
        raise RuntimeError(
            f"Failed to load application settings from {path}"
        ) from error
