# Bromley Bin Reminder

A scheduled service that scrapes the Bromley Council waste-collection website and emails reminders for upcoming bin collections.

## Language

**WasteWorks page**:
The Bromley Council-hosted webpage (`recyclingservices.bromley.gov.uk/waste`) that lists a household's upcoming bin collections. Rendered client-side, so it requires a headless browser rather than a plain HTTP fetch.
_Avoid_: waste page, council page

**Waste Collection**:
A single scheduled pickup of one waste service (e.g. Food Waste) on a specific date, scraped from the WasteWorks page. Modelled by the `WasteCollection` dataclass.
_Avoid_: bin day, pickup, collection event

**Service**:
One of the distinct categories of council-collected waste (Mixed Recycling, Paper & Cardboard, Non-Recyclable Refuse, Food Waste, Garden Waste). Garden Waste is an optional paid service; the others are standard.
_Avoid_: waste type, bin type, category

**Reminder**:
The daily email notification sent for collections that are tomorrow or within the current reminder window. Triggered by the scheduled run comparing scraped collections against the current date.
_Avoid_: notification, alert, email

**Scraper**:
The component (`WasteworksScraper`) that drives a headless Firefox browser via Selenium to render the WasteWorks page and extract collection data with BeautifulSoup.
_Avoid_: crawler, parser

**ENV_FLAG**:
The environment variable selecting how the scraper launches its Firefox WebDriver — `local` (system-installed geckodriver) or `docker` (fixed path to a container-bundled geckodriver). Any other value is treated as unhandled and raises an error.
_Avoid_: environment, mode
