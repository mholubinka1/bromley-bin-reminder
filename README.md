# bromley-bin-reminder

This application checks the [Bromley Council waste website](https://recyclingservices.bromley.gov.uk/waste) on a daily basis and provides automatic notification of upcoming collections for the five types of regular, council-collected waste:

- Mixed Recycling (Cans, Plastics & Glass)
- Paper & Cardboard
- Non-Recyclable Refuse
- Food Waste
- Garden Waste

Note: Garden Waste is an [optional paid service](https://www.bromley.gov.uk/household-waste-recycling/green-garden-waste/2).

## Application Setup

### Logging

Logs are written to stdout and to a rotating file, `bin-reminder.log` (5 MB per file, 5 backups), in the directory named by the `LOG_DIR` environment variable (default `/logs`). Mount a host directory there to keep the logs, for example `/mnt/media/pi-media/containers/bin-reminder/logs:/logs` in `docker-compose.yml`. The directory must be writable by the container user (`sel_user`); if the log file cannot be opened, the app logs to stdout only and prints a warning to stderr.

## E-Mail Setup

## ntfy Setup

Push notifications through [ntfy](https://ntfy.sh) are optional. Add an `ntfy` block to the config file (see `config/config.yml.template`) with a `topic` and, if you self-host, a `server` (defaults to `https://ntfy.sh`). ntfy.sh limits topic names to 64 characters, and anyone who knows a public topic name can read it, so choose something unguessable. Do not put credentials in the server URL, as it can appear in logs.

Each bin gets its own notification, with an emoji for the bin type. The reminder the night before is sent as high priority, and the weekly reminder as default priority. E-mail reminders are unaffected and are sent as before.
