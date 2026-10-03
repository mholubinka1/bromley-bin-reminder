from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import ClassVar

from collection import WasteCollection, print_date
from period import Period

GENERIC_EMOJI_TAG = "put_litter_in_its_place"
SERVICE_NTFY_TAGS = {
    "Mixed Recycling (Cans, Plastics & Glass)": "recycle",
    "Paper & Cardboard": "newspaper",
    "Garden Waste": "fallen_leaf",
    "Non-Recyclable Refuse": "wastebasket",
    "Food Waste": "banana",
}


@dataclass
class NtfyNotification:
    title: str
    message: str
    priority: int
    tags: list[str]


def emoji_tag(service_name: str) -> str:
    return SERVICE_NTFY_TAGS.get(service_name, GENERIC_EMOJI_TAG)


def _build_ntfy_notification(
    collection: WasteCollection, period: Period
) -> NtfyNotification:
    return NtfyNotification(
        title=f"{collection.service_name}: {period.ntfy_title_suffix}",
        message=period.ntfy_message(collection),
        priority=period.ntfy_priority,
        tags=[emoji_tag(collection.service_name)],
    )


def build_ntfy_notifications(
    upcoming_collections: list[WasteCollection], period: Period
) -> list[NtfyNotification]:
    return [
        _build_ntfy_notification(collection, period)
        for collection in upcoming_collections
    ]


class WasteCollectionNotification:
    service_colours: ClassVar[dict[str, str]] = {
        "Mixed Recycling (Cans, Plastics & Glass)": "#006400",
        "Paper & Cardboard": "#00008B",
        "Garden Waste": "#8B4513",
        "Non-Recyclable Refuse": "#000000",
        "Food Waste": "#d0a500",
    }

    email: MIMEMultipart

    def __init__(
        self,
        upcoming_collections: list[WasteCollection],
        now: datetime,
        period: str = "tomorrow",
    ) -> None:
        self._now = now
        self.email = self._create_email(upcoming_collections, period)

    def _tomorrow(self) -> str:
        tomorrow = self._now + timedelta(days=1)
        return print_date(tomorrow)

    def _build_tomorrow_html_body(
        self, upcoming_collections: list[WasteCollection]
    ) -> str:
        table_rows = "".join(f"""
            <tr>
                <td>{collection.service_name}</td>
                <td style="width: 80px;">
                    <div style="width: 80px; height: 30px; background-color: {self.service_colours[collection.service_name]};"></div>
                </td>
            </tr>""" for collection in upcoming_collections)
        tomorrow_str = self._tomorrow()
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{tomorrow_str} - Bin Collections</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f9f9f9;
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                }}
                h2 {{
                    text-align: center;
                    color: #333;
                }}
                table {{
                    width: 80%;
                    margin: 20px auto;
                    border-collapse: collapse;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                th, td {{
                    padding: 12px;
                    text-align: center;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #6a0dad; /* Dark purple background */
                    color: white; /* White text */
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2; /* Light gray for even rows */
                }}
                tr:hover {{
                    background-color: #ddd; /* Highlight on hover */
                }}
            </style>
        </head>
        <body>
            <h1>{tomorrow_str}</h1>
            <h2>Bin Collections</h2>

            <table>
                <thead>
                    <tr>
                        <th colspan="2">Bin Type</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </body>
        </html>
        """
        return html_body

    def _build_week_html_body(self, upcoming_collections: list[WasteCollection]) -> str:
        table_rows = "".join(f"""
            <tr>
                <td>{collection.service_name}</td>
                <td style="width: 80px;">
                    <div style="width: 80px; height: 30px; background-color: {self.service_colours[collection.service_name]};"></div>
                </td>
                <td>{print_date(collection.next_collection_date)}
            </tr>""" for collection in upcoming_collections)
        week_commencing = print_date(self._now)
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Week Commencing: {week_commencing} - Bin Collections</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f9f9f9;
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                }}
                h2 {{
                    text-align: center;
                    color: #333;
                }}
                table {{
                    width: 80%;
                    margin: 20px auto;
                    border-collapse: collapse;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                th, td {{
                    padding: 12px;
                    text-align: center;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #6a0dad; /* Dark purple background */
                    color: white; /* White text */
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2; /* Light gray for even rows */
                }}
                tr:hover {{
                    background-color: #ddd; /* Highlight on hover */
                }}
            </style>
        </head>
        <body>
            <h1>Week Commencing: {week_commencing}</h1>
            <h2>Bin Collections</h2>

            <table>
                <thead>
                    <tr>
                        <th colspan="2">Bin Type</th>
                        <th>Collection Date</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </body>
        </html>
        """
        return html_body

    def _create_email(
        self, upcoming_collections: list[WasteCollection], period: str
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        match (period):
            case "tomorrow":
                msg["Subject"] = "REMINDER: Bins"
                msg["X-Priority"] = "1"
                msg["Importance"] = "high"
                html_body = self._build_tomorrow_html_body(upcoming_collections)
                msg.attach(MIMEText(html_body, "html"))
                return msg
            case "week":
                msg["Subject"] = "Weekly Collections"
                msg["X-Priority"] = "1"
                msg["Importance"] = "high"
                html_body = self._build_week_html_body(upcoming_collections)
                msg.attach(MIMEText(html_body, "html"))
                return msg
            case _:
                raise NotImplementedError(period)
