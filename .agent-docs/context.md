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

**Garden Waste subscription**:
The resident's paid subscription to the Garden Waste Service, with a price, a Renewal date, and whether it renews automatically by direct debit. A household without one has no Garden Waste section on the WasteWorks page. Modelled by the `GardenWasteSubscription` value.
_Avoid_: garden bin plan, membership

**Renewal notice**:
The message, sent over each Channel on the weekly run, that a Garden Waste subscription is due for renewal within the next 30 days, or is overdue (past its Renewal date, which the WasteWorks page still shows for about four weeks). It is separate from a Reminder: it is not about collections and is sent even when no bin is collected that week. When the page says the subscription renews automatically, the notice says so to reassure the resident. No notice is sent while a cancellation or a pending subscription is shown.
_Avoid_: expiry warning, renewal reminder

**Reminder run**:
One scheduled execution for a single Period: scrape the WasteWorks page, select that Period's Waste Collections, and send the Reminder when there are any. A failed run is logged and never stops later runs.
_Avoid_: job, task

**Channel**:
A delivery route for Reminders and Renewal notices: email (SMTP) or ntfy. Email is always configured; ntfy is optional. Channels are independent — one failing does not block the other.
_Avoid_: transport, medium

**ntfy**:
The push-notification service (ntfy.sh by default) that delivers Reminders to subscribed phones via a topic. Sends one notification per Service, each tagged with that Service's emoji; night-before notifications are high priority.
_Avoid_: push, ntfy notification

**Topic**:
The ntfy channel name a Reminder is published to. Effectively a secret on public ntfy.sh (anyone knowing it can subscribe), so it lives in the config file, never in the repo. Limited to 64 characters on ntfy.sh.
_Avoid_: channel, room

**Scraper**:
The component (`WasteworksScraper`) that obtains the WasteWorks page from a Page source and extracts the Waste Collections from its HTML with BeautifulSoup, resolving each collection date against the current date.
_Avoid_: crawler, parser

**Page source**:
Where the Scraper gets the rendered WasteWorks page HTML from: a headless Firefox browser driven via Selenium in production, saved HTML in tests.
_Avoid_: fetcher, downloader, driver

**ENV_FLAG**:
The environment variable selecting how the Selenium Page source launches its Firefox WebDriver — `local` (system-installed geckodriver) or `docker` (fixed path to a container-bundled geckodriver). Any other value is treated as unhandled and raises an error.
_Avoid_: environment, mode
