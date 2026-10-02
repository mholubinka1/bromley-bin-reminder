# bromley-bin-reminder

This application checks the [Bromley Council waste website](https://recyclingservices.bromley.gov.uk/waste) on a daily basis and provides automatic notification of upcoming collections for the five types of regular, council-collected waste:

- Mixed Recycling (Cans, Plastics & Glass)
- Paper & Cardboard
- Non-Recyclable Refuse
- Food Waste
- Garden Waste

Note: Garden Waste is an [optional paid service](https://www.bromley.gov.uk/household-waste-recycling/green-garden-waste/2).

## Application Setup

## E-Mail Setup

## ntfy Setup

Push notifications through [ntfy](https://ntfy.sh) are optional. Add an `ntfy` block to the config file (see `config/config.yml.template`) with a `topic` and, if you self-host, a `server` (defaults to `https://ntfy.sh`). ntfy.sh limits topic names to 64 characters, and anyone who knows a public topic name can read it, so choose something unguessable.

Each bin gets its own notification, with an emoji for the bin type. The reminder the night before is sent as high priority, and the weekly reminder as default priority. E-mail reminders are unaffected and are sent as before.
