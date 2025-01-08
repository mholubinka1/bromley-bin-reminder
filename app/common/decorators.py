import logging.config
import time
from logging import Logger, getLogger
from typing import Any, Callable, Optional

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


def retry(
    stop_after: int = 3, retry_delay: int = 10
) -> Callable[[Callable[..., Optional[Any]]], Callable[..., Any]]:
    def decorator(func: Callable[..., Optional[Any]]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            while attempt < stop_after:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error = f"Error attempting to execute {func}: {e}. \nRetrying in {retry_delay} seconds."
                    logger.warning(error)
                    attempt += 1
                    time.sleep(retry_delay)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = f"Error attempting to execute {func}: {e}. \nRetries exhausted."
                logger.error(error)
                raise e

        return wrapper

    return decorator
