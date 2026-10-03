import email
import re
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from typing import Any
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from collection import WasteCollection
from notification import NtfyNotification

LONDON = ZoneInfo("Europe/London")
FRIDAY_EVENING = datetime(2026, 10, 2, 18, 0, tzinfo=LONDON)


def a_collection(
    service_name: str,
    day: int = 3,
    is_tomorrow: bool = True,
    is_this_week: bool = True,
) -> WasteCollection:
    return WasteCollection(
        service_name=service_name,
        next_collection_date=datetime(2026, 10, day, tzinfo=LONDON),
        is_tomorrow=is_tomorrow,
        is_this_week=is_this_week,
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


def a_notification(title: str = "Food Waste: tomorrow") -> NtfyNotification:
    return NtfyNotification(
        title=title,
        message="Put it out tonight.",
        priority=4,
        tags=["banana"],
    )


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
        self._in_body_row = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open_tag = tag
        if tag == "tr":
            self._in_body_row = True
            self.rows.append([])
        if tag == "div":
            style = dict(attrs).get("style") or ""
            colour = re.search(r"background-color:\s*(#\w+)", style)
            if colour and self._in_body_row:
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
        elif self._open_tag == "td" and self._in_body_row:
            self.rows[-1].append(text)


def sent_email(smtp: MagicMock) -> SentEmail:
    raw_message = smtp.return_value.sendmail.call_args.args[2]
    message = email.message_from_string(raw_message)
    html_part = message.get_payload(0).get_payload(decode=True).decode()  # type: ignore[union-attr]
    reader = _EmailHtmlReader()
    reader.feed(html_part)
    return SentEmail(
        subject=message["Subject"],
        x_priority=message["X-Priority"],
        importance=message["Importance"],
        title=reader.title,
        heading=reader.heading,
        header_cells=reader.header_cells,
        rows=[row for row in reader.rows if row],
    )
