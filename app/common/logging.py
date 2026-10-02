import os
import sys
from pathlib import Path
from typing import Any

APP_LOGGER_NAME = "bromley-bin-reminder"
LOG_LEVEL = "DEBUG"
LOG_DIR_ENV = "LOG_DIR"
DEFAULT_LOG_DIR = "/logs"
LOG_FILE_NAME = "bin-reminder.log"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5


def build_config(log_dir: str) -> dict[str, Any]:
    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
            "level": LOG_LEVEL,
        },
    }
    log_file = Path(log_dir) / LOG_FILE_NAME
    if not _can_write_log_file(log_file):
        print(
            f"Cannot write log file [{log_file}]; logging to console only.",
            file=sys.stderr,
        )
    else:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": str(log_file),
            "maxBytes": LOG_MAX_BYTES,
            "backupCount": LOG_BACKUP_COUNT,
            "encoding": "utf-8",
            "level": LOG_LEVEL,
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": handlers,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "loggers": {
            APP_LOGGER_NAME: {
                "handlers": list(handlers),
                "level": LOG_LEVEL,
                "propagate": False,
            }
        },
    }


def _can_write_log_file(log_file: Path) -> bool:
    try:
        with open(log_file, "a", encoding="utf-8"):
            return True
    except OSError:
        return False


config = build_config(os.environ.get(LOG_DIR_ENV, DEFAULT_LOG_DIR))
