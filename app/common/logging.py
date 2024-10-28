APP_LOGGER_NAME = "bromley-bin-reminder"
LOG_LEVEL = "DEBUG"

config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "std_out",
            "stream": "ext://sys.stdout",
            "level": LOG_LEVEL,
        },
    },
    "formatters": {
        "std_out": {
            "format": "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "loggers": {
        APP_LOGGER_NAME: {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        }
    },
}
