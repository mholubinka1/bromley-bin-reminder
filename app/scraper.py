import os
import re
from collections.abc import Callable
from datetime import datetime
from logging import Logger, getLogger
from typing import Protocol

from bs4 import BeautifulSoup, Tag
from collection import WasteCollection
from common.decorators import retry
from common.logging import APP_LOGGER_NAME
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from subscription import GardenWasteSubscription

logger: Logger = getLogger(APP_LOGGER_NAME)

NEXT_COLLECTION_LABEL = "Next collection"
SUBSCRIPTION_LABEL = "Subscription"
RENEWAL_LABEL = "Renewal"
GARDEN_WASTE_SERVICE = "Garden Waste"
RENEWAL_DATE_PATTERN = re.compile(r"\d{1,2} [A-Za-z]+ \d{4}")
RENEWS_AUTOMATICALLY_TEXT = "will renew automatically"
IN_PROGRESS_TEXTS = (  # lowercase: compared against the lowercased section text
    "cancellation in progress",
    "pending garden subscription",
    "pending direct debit subscription",
)


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
    month_name = date.split()[-1] if date else ""
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


def find_service_row(
    service: Tag, following_service: Tag | None, label: str
) -> Tag | None:
    """Find the service's own row with this label, never one belonging to a later service."""
    for element in service.next_elements:
        if element is following_service:
            return None
        if (
            isinstance(element, Tag)
            and element.name == "dt"
            and element.string == label
        ):
            return element
    return None


def section_text(service: Tag) -> str:
    """All the text of the service's own section on the page, whitespace-normalised."""
    section = service.find_parent("div", class_="waste-service-grid")
    if section is None:
        logger.warning(
            f"Could not find the section of {service.get_text(strip=True)}; "
            "a pending subscription or cancellation will not be detected."
        )
        return ""
    return " ".join(section.get_text().split())


def row_text(row: Tag) -> str:
    value = row.find_next_sibling("dd")
    return " ".join(value.get_text().split()) if value else ""


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
        following_services = [*services[1:], None]
        collections: list[WasteCollection] = []
        for service, following_service in zip(services, following_services):
            service_name = service.get_text(strip=True)
            next_collection = find_service_row(
                service, following_service, NEXT_COLLECTION_LABEL
            )
            if next_collection:
                next_collection_date = parse_date(
                    row_text(next_collection),
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

    def get_garden_waste_subscription(self) -> GardenWasteSubscription | None:
        html = self._page_source.render(self._target_url)
        soup = BeautifulSoup(html, "html.parser")
        services = soup.find_all("h3", class_="govuk-heading-m waste-service-name")
        following_services = [*services[1:], None]
        for service, following_service in zip(services, following_services):
            if service.get_text(strip=True) == GARDEN_WASTE_SERVICE:
                return self._read_subscription(service, following_service)
        return None

    def _read_subscription(
        self, service: Tag, following_service: Tag | None
    ) -> GardenWasteSubscription | None:
        renewal_row = find_service_row(service, following_service, RENEWAL_LABEL)
        subscription_row = find_service_row(
            service, following_service, SUBSCRIPTION_LABEL
        )
        if renewal_row is None and subscription_row is None:
            return None  # no subscription rows: not subscribed, nothing to warn about
        if renewal_row is None or subscription_row is None:
            logger.warning(
                "Could not read the Garden Waste renewal: the Subscription or "
                "Renewal row is missing."
            )
            return None
        renewal_text = row_text(renewal_row)
        renewal_date = self._parse_renewal_date(renewal_text)
        if renewal_date is None:
            logger.warning(
                f"Could not read the Garden Waste renewal: no date in [{renewal_text}]."
            )
            return None
        text = section_text(service)
        return GardenWasteSubscription(
            renewal_date=renewal_date,
            subscription_text=row_text(subscription_row),
            renews_automatically=RENEWS_AUTOMATICALLY_TEXT in text,
            in_progress=any(marker in text.lower() for marker in IN_PROGRESS_TEXTS),
        )

    def _parse_renewal_date(self, renewal_text: str) -> datetime | None:
        """The leading date of the Renewal row; trailing notes are not part of it."""
        match = RENEWAL_DATE_PATTERN.match(renewal_text)
        if match is None:
            return None
        try:
            return datetime.strptime(match.group(), "%d %B %Y").replace(
                tzinfo=self._clock().tzinfo
            )
        except ValueError:
            return None
