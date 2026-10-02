import logging.config
import os
import time
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class ConfigChangePoller:
    _path: str
    _command: list[str]
    _last_modified_time: float
    _monitoring: bool

    def __init__(self, path: str, command: list[str]) -> None:
        self._path = path
        self._command = command
        self._last_modified_time = os.path.getmtime(self._path)
        self._monitoring = True

    def start(self) -> None:
        self._monitoring = True

    def poll(self) -> None:
        while self._monitoring:
            try:
                current_modified_time = os.path.getmtime(self._path)
                if current_modified_time != self._last_modified_time:
                    logger.info(
                        f"Config change detected: {self._path}. Restarting application."
                    )
                    self._last_modified_time = current_modified_time
                    # Replace this process in place so the old instance can never
                    # keep running (and writing the shared log file) beside the new one.
                    os.execvp(self._command[0], self._command)
            except FileNotFoundError:
                logger.error("Config file not found.")
            except Exception:
                logger.exception("Error polling config file.")
            finally:
                time.sleep(1)

    def stop(self) -> None:
        self._monitoring = False
