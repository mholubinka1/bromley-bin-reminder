import logging.config
import os
import re
from datetime import datetime
from logging import Logger, getLogger
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
from collection import WasteCollection, is_collection_this_week, is_collection_tomorrow
from common.decorators import retry
from common.logging import APP_LOGGER_NAME, config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


def parse_date(date: str) -> Tuple[bool, bool, datetime]:
    date = re.sub(r"\(.*?\)", "", date)
    date = re.sub(r"\s*\(In Progress\)", "", date)
    date = re.sub(r"\b(\d+)(th|rd|nd|st)\b", r"\1", date)
    date = date.strip()
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    parsed_date = datetime.strptime(date, "%A, %d %B")
    collection_month = parsed_date.month
    if current_month == 12 and collection_month == 1:
        target_year = current_year + 1
    else:
        target_year = current_year
    collection_date = datetime.strptime(f"{date} {target_year}", "%A, %d %B %Y")
    is_tomorrow = is_collection_tomorrow(
        current_date=current_date, collection_date=collection_date
    )
    is_this_week = is_collection_this_week(
        current_date=current_date, collection_date=collection_date
    )
    return (is_tomorrow, is_this_week, collection_date)


class WasteworksScraper:  # DynamicHTMLScraper
    _target_url: str
    _chrome_web_driver: webdriver.Firefox

    def __init__(self, target_url: str) -> None:
        self._target_url = target_url

    def _create_firefox_web_driver(self) -> webdriver.Firefox:
        env_flag = os.environ.get("ENV_FLAG")
        match (os.environ.get("ENV_FLAG")):
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
    def _render_web_page(self) -> Optional[str]:
        driver = self._create_firefox_web_driver()
        driver.get(self._target_url)
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
        except Exception as e:
            driver.quit()
            logger.exception(e)
            raise Exception(f"Failed to render Wasteworks page: {self._target_url}")

    def _extract_collections(self, soup: BeautifulSoup) -> List[WasteCollection]:
        logger.info("Extracting upcoming collection information.")
        services = soup.find_all("h3", class_="govuk-heading-m waste-service-name")
        collections: List[WasteCollection] = []
        for service in services:
            service_name = service.get_text(strip=True)
            next_collection = service.find_next("dt", string="Next collection")  # type: ignore[call-overload]
            if next_collection:
                is_tomorrow, is_this_week, next_collection_date = parse_date(
                    next_collection.find_next_sibling("dd").get_text(strip=True)
                )
                collections.append(
                    WasteCollection(
                        service_name=service_name,
                        next_collection_date=next_collection_date,
                        is_tomorrow=is_tomorrow,
                        is_this_week=is_this_week,
                    )
                )
        logger.info(f"Found data for {len(collections)} upcoming collections.")
        return collections

    def get_upcoming_collections(self) -> List[WasteCollection]:
        html = self._render_web_page()
        soup = BeautifulSoup(html, "html.parser")
        return self._extract_collections(soup)
