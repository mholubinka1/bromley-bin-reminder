from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from waste_utils import WasteCollection


class WasteCollectionNotification:
    service_colours = {
        "Mixed Recycling (Cans, Plastics & Glass)": "#006400",
        "Paper & Cardboard": "#00008B",
        "Garden Waste": "#8B4513",
        "Non-Recyclable Refuse": "#000000",
        "Food Waste": "#d0a500",
    }

    email: MIMEMultipart

    def __init__(
        self, upcoming_collections: List[WasteCollection], period: str = "tomorrow"
    ) -> None:
        self.email = self._create_email(upcoming_collections, period)

    def _print_date(self, date: datetime) -> str:
        day = date.day
        day_suffix = "th"
        if day in [1, 21, 31]:
            day_suffix = "st"
        elif day in [2, 22]:
            day_suffix = "nd"
        elif day in [3, 23]:
            day_suffix = "rd"
        return date.strftime(f"%A {day}{day_suffix} %B")

    def _tomorrow(self) -> str:
        tomorrow = datetime.now() + timedelta(days=1)
        return self._print_date(tomorrow)

    def _build_tomorrow_html_body(
        self, upcoming_collections: List[WasteCollection]
    ) -> str:
        table_rows = "".join(
            f"""
            <tr>
                <td>{collection.service_name}</td>
                <td style="width: 80px;">
                    <div style="width: 80px; height: 30px; background-color: {self.service_colours[collection.service_name]};"></div>
                </td>
            </tr>"""
            for collection in upcoming_collections
        )
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

    def _build_week_html_body(self, upcoming_collections: List[WasteCollection]) -> str:
        table_rows = "".join(
            f"""
            <tr>
                <td>{collection.service_name}</td>
                <td style="width: 80px;">
                    <div style="width: 80px; height: 30px; background-color: {self.service_colours[collection.service_name]};"></div>
                </td>
                <td>{self._print_date(collection.next_collection_date)}
            </tr>"""
            for collection in upcoming_collections
        )
        week_commencing = self._print_date(datetime.now())
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
        self, upcoming_collections: List[WasteCollection], period: str
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

    def _create_push(self, upcoming_collections: List[WasteCollection]) -> None:
        pass
