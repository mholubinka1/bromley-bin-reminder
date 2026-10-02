import logging.config
from pathlib import Path

from common.logging import APP_LOGGER_NAME, LOG_FILE_NAME, build_config


def test_file_handler_writes_to_the_log_directory_alongside_the_console(
    tmp_path: Path,
) -> None:
    # Given a writable log directory
    # When the logging config is built
    config = build_config(str(tmp_path))

    # Then a rotating file handler targets the log file and the console is kept
    handler = config["handlers"]["file"]
    assert handler["class"] == "logging.handlers.RotatingFileHandler"
    assert handler["filename"] == str(tmp_path / LOG_FILE_NAME)
    assert config["loggers"][APP_LOGGER_NAME]["handlers"] == ["console", "file"]


def test_file_handler_rotates_with_bounded_size_and_backups(tmp_path: Path) -> None:
    # Given a writable log directory
    # When the logging config is built
    handler = build_config(str(tmp_path))["handlers"]["file"]

    # Then rotation is bounded
    assert handler["maxBytes"] > 0
    assert handler["backupCount"] > 0


def test_messages_are_written_to_the_log_file(tmp_path: Path) -> None:
    # Given logging configured against a writable directory
    logging.config.dictConfig(build_config(str(tmp_path)))

    # When the app logger logs a message
    logging.getLogger(APP_LOGGER_NAME).info("hello bins")
    for handler in logging.getLogger(APP_LOGGER_NAME).handlers:
        handler.flush()

    # Then it appears in the log file
    assert "hello bins" in (tmp_path / LOG_FILE_NAME).read_text()


def test_console_only_when_the_log_directory_is_missing(tmp_path: Path) -> None:
    # Given a log directory that does not exist
    missing = tmp_path / "nope"

    # When the logging config is built
    config = build_config(str(missing))

    # Then only the console handler is configured and nothing is created
    assert "file" not in config["handlers"]
    assert config["loggers"][APP_LOGGER_NAME]["handlers"] == ["console"]
    assert not missing.exists()


def test_console_only_when_the_log_directory_is_not_writable(tmp_path: Path) -> None:
    # Given a read-only log directory
    tmp_path.chmod(0o500)
    try:
        # When the logging config is built
        config = build_config(str(tmp_path))
    finally:
        tmp_path.chmod(0o700)

    # Then only the console handler is configured
    assert "file" not in config["handlers"]
