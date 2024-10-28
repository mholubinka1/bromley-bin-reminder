import logging.config
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config
from selenium import webdriver

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class DynamicHTMLScraper:
    _target_url: str

    def __init__(self, target_url: str) -> None:
        self._target_url = target_url
        self._chrome_driver_path = "usr/bin/chromedriver"

    def render_web_page(self) -> None:
        driver = webdriver.Chrome(executable_path=self._chrome_driver_path)
        driver.get(self._target_url)
        logger.info(f"Page title: {driver.title}")
        driver.quit()
