import logging.config
import time
from collections.abc import Callable
from logging import Logger, getLogger
from typing import Any

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


def retry(
    stop_after: int = 3, retry_delay: int = 10
) -> Callable[[Callable[..., Any | None]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any | None]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            while attempt < stop_after:
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # noqa: BLE001
                    error = f"Error attempting to execute {func}: {e}. \nRetrying in {retry_delay} seconds."
                    logger.warning(error)
                    attempt += 1
                    time.sleep(retry_delay)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = f"Error attempting to execute {func}: {e}. \nRetries exhausted."
                logger.error(error)
                raise

        return wrapper

    return decorator
