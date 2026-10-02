import os
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
            "formatter": "std_out",
            "stream": "ext://sys.stdout",
            "level": LOG_LEVEL,
        },
    }
    if _is_writable_dir(log_dir):
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "std_out",
            "filename": str(Path(log_dir) / LOG_FILE_NAME),
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
            "std_out": {
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


def _is_writable_dir(path: str) -> bool:
    return os.path.isdir(path) and os.access(path, os.W_OK)


config = build_config(os.environ.get(LOG_DIR_ENV, DEFAULT_LOG_DIR))
