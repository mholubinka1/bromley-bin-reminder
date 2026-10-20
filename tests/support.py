import email
import re
from dataclasses import dataclass
from datetime import datetime
from email.message import Message
from html.parser import HTMLParser
from typing import Any
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from collection import WasteCollection
from period import Period

LONDON = ZoneInfo("Europe/London")
FRIDAY_EVENING = datetime(2026, 10, 2, 18, 0, tzinfo=LONDON)


def a_collection(service_name: str, day: int = 3) -> WasteCollection:
    return WasteCollection(
        service_name=service_name,
        next_collection_date=datetime(2026, 10, day, tzinfo=LONDON),
    )


def yaml_settings(**extra: Any) -> dict[str, Any]:
    return {
        "remind": {
            "url": "https://example.com/collections",
            "email_addresses": ["resident@example.com"],
            "time": "18:00",
        },
        "smtp": {
            "username": "bins@example.com",
            "password": "secret",
            "server": "smtp.example.com",
            "port": 587,
        },
        **extra,
    }


@dataclass
class SentEmail:
    subject: str
    x_priority: str | None
    importance: str | None
    title: str
    heading: str
    header_cells: list[str]
    rows: list[list[str]]


class _EmailHtmlReader(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.heading = ""
        self.header_cells: list[str] = []
        self.rows: list[list[str]] = []
        self._open_tag: str | None = None
        self._in_row = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open_tag = tag
        if tag == "tr":
            self._in_row = True
            self.rows.append([])
        if tag == "div":
            style = dict(attrs).get("style") or ""
            colour = re.search(r"background-color:\s*(#\w+)", style)
            if colour and self._in_row:
                self.rows[-1].append(colour.group(1))

    def handle_endtag(self, tag: str) -> None:
        self._open_tag = None

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._open_tag == "title":
            self.title += text
        elif self._open_tag == "h1":
            self.heading += text
        elif self._open_tag == "th":
            self.header_cells.append(text)
        elif self._open_tag == "td" and self._in_row:
            self.rows[-1].append(text)


def _sent_message(smtp: MagicMock) -> Message:
    return email.message_from_string(smtp.return_value.sendmail.call_args.args[2])


def sent_email_html(smtp: MagicMock) -> str:
    html_part = _sent_message(smtp).get_payload(0)
    return html_part.get_payload(decode=True).decode()  # type: ignore[union-attr]


def sent_email(smtp: MagicMock) -> SentEmail:
    message = _sent_message(smtp)
    reader = _EmailHtmlReader()
    reader.feed(sent_email_html(smtp))
    return SentEmail(
        subject=message["Subject"],
        x_priority=message["X-Priority"],
        importance=message["Importance"],
        title=reader.title,
        heading=reader.heading,
        header_cells=reader.header_cells,
        rows=[row for row in reader.rows if row],
    )


class FakeScraper:
    def __init__(self, collections: list[WasteCollection]) -> None:
        self._collections = collections

    def get_upcoming_collections(self) -> list[WasteCollection]:
        return self._collections


class FailingScraper:
    def get_upcoming_collections(self) -> list[WasteCollection]:
        raise RuntimeError("WasteWorks page could not be rendered")


def a_wasteworks_page(*services: tuple[str, str | None]) -> str:
    """Render a WasteWorks page laid out like the real one.

    Each service sits in its own grid with its heading and its rows. A None date gives a
    service whose only row is a cost, like the real page's unscheduled services.
    """
    sections = []
    for service_name, next_collection in services:
        rows = (
            '<dl class="govuk-summary-list">'
            "<div><dt>Frequency</dt><dd>Every week</dd></div>"
            f"<div><dt>Next collection</dt><dd>{next_collection}</dd></div>"
            "<div><dt>Last collection</dt><dd>Friday, 25th September</dd></div>"
            "</dl>"
            if next_collection is not None
            else '<dl class="govuk-summary-list"><div><dt>Cost</dt><dd>From £43.00</dd></div></dl>'
        )
        sections.append(
            '<div class="waste-service-grid">'
            '<div class="waste-service-grid--service-name">'
            f'<h3 class="govuk-heading-m waste-service-name">{service_name}</h3>'
            f"</div>{rows}</div>"
        )
    return (
        '<html><body><div class="govuk-grid-row">'
        f'<div class="govuk-grid-column-two-thirds">{"".join(sections)}</div>'
        "</div></body></html>"
    )


class RecordingChannel:
    def __init__(self, name: str, sent: list[str]) -> None:
        self._name = name
        self._sent = sent
        self.reminders: list[tuple[list[WasteCollection], datetime, Period]] = []

    def send(
        self, collections: list[WasteCollection], now: datetime, period: Period
    ) -> None:
        self.reminders.append((collections, now, period))
        self._sent.append(self._name)


class FixturePageSource:
    def __init__(self, html: str) -> None:
        self._html = html

    def render(self, url: str) -> str:
        return self._html
