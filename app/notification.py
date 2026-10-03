from dataclasses import dataclass
from datetime import datetime
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


EMAIL_PRIORITY_HEADERS = {"X-Priority": "1", "Importance": "high"}

EMAIL_TEMPLATE = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{heading} - Bin Collections</title>
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
            <h1>{heading}</h1>
            <h2>Bin Collections</h2>

            <table>
                <thead>
                    <tr>
                        <th colspan="2">Bin Type</th>{date_header}
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </body>
        </html>
        """

COLLECTION_DATE_HEADER = """
                        <th>Collection Date</th>"""

TABLE_ROW_TEMPLATE = """
            <tr>
                <td>{service_name}</td>
                <td style="width: 80px;">
                    <div style="width: 80px; height: 30px; background-color: {colour};"></div>
                </td>{date_cell}
            </tr>"""

COLLECTION_DATE_CELL = """
                <td>{collection_date}</td>"""


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
        period: Period,
    ) -> None:
        self._now = now
        self.email = self._create_email(upcoming_collections, period)

    def _build_table_row(self, collection: WasteCollection, period: Period) -> str:
        date_cell = (
            COLLECTION_DATE_CELL.format(
                collection_date=print_date(collection.next_collection_date)
            )
            if period.shows_collection_dates
            else ""
        )
        return TABLE_ROW_TEMPLATE.format(
            service_name=collection.service_name,
            colour=self.service_colours[collection.service_name],
            date_cell=date_cell,
        )

    def _build_html_body(
        self, upcoming_collections: list[WasteCollection], period: Period
    ) -> str:
        return EMAIL_TEMPLATE.format(
            heading=period.email_heading(self._now),
            date_header=COLLECTION_DATE_HEADER if period.shows_collection_dates else "",
            table_rows="".join(
                self._build_table_row(collection, period)
                for collection in upcoming_collections
            ),
        )

    def _create_email(
        self, upcoming_collections: list[WasteCollection], period: Period
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["Subject"] = period.email_subject
        for header, value in EMAIL_PRIORITY_HEADERS.items():
            msg[header] = value
        msg.attach(
            MIMEText(self._build_html_body(upcoming_collections, period), "html")
        )
        return msg
