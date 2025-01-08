import logging.config
import os
import subprocess
from logging import Logger, getLogger
from typing import List

from common.logging import APP_LOGGER_NAME, config
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class RestartOnConfigChangeHandler(FileSystemEventHandler):  # type: ignore
    _path: str
    _command: List[str]

    def __init__(self, path: str, command: List) -> None:
        self._path = path
        self._command = command

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        path = (
            event.src_path.decode("utf-8")
            if isinstance(event.src_path, bytes)
            else event.src_path
        )
        if os.path.normpath(path) == os.path.normpath(self._path):
            logger.info(f"Change detected: {path}. Restarting application.")
            subprocess.Popen(self._command)
            exit(0)
