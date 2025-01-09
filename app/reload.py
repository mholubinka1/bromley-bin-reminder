import logging.config
import os
import subprocess
import time
from logging import Logger, getLogger
from typing import List

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class ConfigChangePoller:
    _path: str
    _command: List[str]
    _last_modified_time: float
    _monitoring: bool

    def __init__(self, path: str, command: List) -> None:
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
                    subprocess.Popen(self._command)
                    exit(0)
            except FileNotFoundError:
                logger.error("Config file not found.")
            except Exception:
                logger.error("Error polling config file.")
            finally:
                time.sleep(1)

    def stop(self) -> None:
        self._monitoring = False
