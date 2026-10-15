import logging.config
import os
import re
from collections.abc import Callable
from datetime import datetime
from logging import Logger, getLogger
from typing import Protocol

from bs4 import BeautifulSoup
from collection import WasteCollection
from common.decorators import retry
from common.logging import APP_LOGGER_NAME, config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class ScraperError(Exception):
    pass


class PageSource(Protocol):
    def render(self, url: str) -> str: ...


class SeleniumPageSource:
    def _create_firefox_web_driver(self) -> webdriver.Firefox:
        env_flag = os.environ.get("ENV_FLAG")
        match env_flag:
            case "local":
                service = webdriver.FirefoxService()
            case "docker":
                service = webdriver.FirefoxService(
                    executable_path="/usr/local/bin/geckodriver"
                )
            case _:
                raise NotImplementedError(f"Unhandled ENV_FLAG: {env_flag}")
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Firefox(service=service, options=options)
        return driver

    @retry()
    def render(self, url: str) -> str:
        driver = self._create_firefox_web_driver()
        driver.get(url)
        try:
            wait = WebDriverWait(driver, 300)
            _ = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@class='govuk-heading-m waste-service-name']")
                )
            )
            logger.info("Rendered WasteWorks webpage.")
            page_source = driver.page_source
            driver.quit()
            return page_source
        except Exception:
            driver.quit()
            logger.exception(f"Failed to render Wasteworks page: {url}")
            raise ScraperError(f"Failed to render Wasteworks page: {url}")


def parse_date(date: str, now: datetime) -> datetime:
    date = re.sub(r"\(.*?\)", "", date)
    date = re.sub(r"\b(\d+)(th|rd|nd|st)\b", r"\1", date)
    date = date.strip()
    current_year = now.year
    current_month = now.month
    month_name = date.rpartition(" ")[2]
    collection_month = (
        datetime.strptime(month_name, "%B").replace(tzinfo=now.tzinfo).month
    )
    if current_month == 12 and collection_month == 1:
        target_year = current_year + 1
    else:
        target_year = current_year
    collection_date = datetime.strptime(
        f"{date} {target_year}", "%A, %d %B %Y"
    ).replace(tzinfo=now.tzinfo)
    return collection_date


class WasteworksScraper:
    _page_source: PageSource
    _target_url: str
    _clock: Callable[[], datetime]

    def __init__(
        self,
        page_source: PageSource,
        target_url: str,
        clock: Callable[[], datetime],
    ) -> None:
        self._page_source = page_source
        self._target_url = target_url
        self._clock = clock

    def _extract_collections(
        self, soup: BeautifulSoup, now: datetime
    ) -> list[WasteCollection]:
        logger.info("Extracting upcoming collection information.")
        services = soup.find_all("h3", class_="govuk-heading-m waste-service-name")
        collections: list[WasteCollection] = []
        for service in services:
            service_name = service.get_text(strip=True)
            next_collection = service.find_next("dt", string="Next collection")  # type: ignore[call-overload]
            if next_collection:
                next_collection_date = parse_date(
                    next_collection.find_next_sibling("dd").get_text(strip=True),
                    now,
                )
                collections.append(
                    WasteCollection(
                        service_name=service_name,
                        next_collection_date=next_collection_date,
                    )
                )
        logger.info(f"Found data for {len(collections)} upcoming collections.")
        return collections

    def get_upcoming_collections(self) -> list[WasteCollection]:
        html = self._page_source.render(self._target_url)
        soup = BeautifulSoup(html, "html.parser")
        return self._extract_collections(soup, self._clock())
