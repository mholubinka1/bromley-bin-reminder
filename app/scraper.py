import logging.config
import time
from logging import Logger, getLogger
from typing import Any, Callable, List, Optional

from bs4 import BeautifulSoup
from common.logging import APP_LOGGER_NAME, config
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from waste_utils import WasteCollection, parse_date
from webdriver_manager.chrome import ChromeDriverManager

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


class WasteworksScraper:  # DynamicHTMLScraper
    _target_url: str
    _chrome_web_driver: webdriver.Chrome

    def __init__(self, target_url: str) -> None:
        self._target_url = target_url

    def _create_chrome_web_driver(self) -> webdriver.Chrome:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    @retry()
    def _render_web_page(self) -> Optional[str]:
        driver = self._create_chrome_web_driver()
        driver.get(self._target_url)
        try:
            wait = WebDriverWait(driver, 300)
            _ = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@class='govuk-heading-m waste-service-name']")
                )
            )
            page_source = driver.page_source
            driver.quit()
            return page_source
        except Exception as e:
            driver.quit()
            logger.exception(e)
            raise Exception(f"Failed to render Wasteworks page: {self._target_url}")

    def _extract_collections(self, soup: BeautifulSoup) -> List[WasteCollection]:
        services = soup.find_all("h3", class_="govuk-heading-m waste-service-name")
        collections: List[WasteCollection] = []
        for service in services:
            service_name = service.get_text(strip=True)
            next_collection = service.find_next("dt", string="Next collection")
            if next_collection:
                is_tomorrow, next_collection_date = parse_date(
                    next_collection.find_next_sibling("dd").get_text(strip=True)
                )
                collections.append(
                    WasteCollection(
                        service_name=service_name,
                        next_collection_date=next_collection_date,
                        is_tomorrow=is_tomorrow,
                    )
                )
        return collections

    def get_upcoming_collections(self) -> List[WasteCollection]:
        html = self._render_web_page()
        soup = BeautifulSoup(html, "html.parser")
        return self._extract_collections(soup)
