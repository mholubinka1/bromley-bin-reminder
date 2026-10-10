# Bromley Bin Reminder

A scheduled service that scrapes the Bromley Council waste-collection website and sends email and ntfy reminders for upcoming bin collections.

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
The scheduled message sent for collections that are tomorrow (nightly) or within the current reminder window (weekly, Sundays). Delivered over each configured Channel. Triggered by the scheduled run comparing scraped collections against the current date.
_Avoid_: alert

**Period**:
The span a Reminder covers: Tomorrow (the nightly Reminder) or Week (the weekly Reminder, sent on Sundays). A Period decides which Waste Collections a Reminder includes and how that Reminder is worded.
_Avoid_: schedule, frequency, mode

**Reminder run**:
One scheduled execution for a single Period: scrape the WasteWorks page, select that Period's Waste Collections, and send the Reminder when there are any. A failed run is logged and never stops later runs.
_Avoid_: job, task

**Channel**:
A delivery route for Reminders: email (SMTP) or ntfy. Email is always configured; ntfy is optional. Channels are independent — one failing does not block the other.
_Avoid_: transport, medium

**ntfy**:
The push-notification service (ntfy.sh by default) that delivers Reminders to subscribed phones via a topic. Sends one notification per Service, each tagged with that Service's emoji; night-before notifications are high priority.
_Avoid_: push, ntfy notification

**Topic**:
The ntfy channel name a Reminder is published to. Effectively a secret on public ntfy.sh (anyone knowing it can subscribe), so it lives in the config file, never in the repo. Limited to 64 characters on ntfy.sh.
_Avoid_: channel, room

**Scraper**:
The component (`WasteworksScraper`) that drives a headless Firefox browser via Selenium to render the WasteWorks page and extract collection data with BeautifulSoup.
_Avoid_: crawler, parser

**ENV_FLAG**:
The environment variable selecting how the scraper launches its Firefox WebDriver — `local` (system-installed geckodriver) or `docker` (fixed path to a container-bundled geckodriver). Any other value is treated as unhandled and raises an error.
_Avoid_: environment, mode
