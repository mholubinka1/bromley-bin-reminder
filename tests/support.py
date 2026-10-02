from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from collection import WasteCollection
from notification import NtfyNotification

LONDON = ZoneInfo("Europe/London")


def a_collection(service_name: str, day: int = 3) -> WasteCollection:
    return WasteCollection(
        service_name=service_name,
        next_collection_date=datetime(2026, 10, day, tzinfo=LONDON),
        is_tomorrow=True,
        is_this_week=True,
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
