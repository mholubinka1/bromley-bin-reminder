import logging.config
from datetime import datetime
from logging import Logger, getLogger

from logging_config import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")

today = datetime.today().date()
print(today)
