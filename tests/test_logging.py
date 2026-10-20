import logging.config
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import common.logging
import pytest
from common.logging import (
    APP_LOGGER_NAME,
    LOG_DIR_ENV,
    LOG_FILE_NAME,
    build_config,
    configure_logging,
)


@pytest.fixture
def restore_app_logger() -> Iterator[None]:
    logger = logging.getLogger(APP_LOGGER_NAME)
    original = list(logger.handlers)
    propagate, level = logger.propagate, logger.level
    yield
    for handler in logger.handlers:
        if handler not in original:
            handler.close()
    logger.handlers = original
    logger.propagate, logger.level = propagate, level


def test_configuring_logging_sets_up_the_console_and_file_handlers(
    tmp_path: Path, restore_app_logger: None
) -> None:
    # Given a writable log directory
    # When logging is configured
    configure_logging(str(tmp_path))

    # Then the app logger writes to the console and the log file, without propagating
    logger = logging.getLogger(APP_LOGGER_NAME)
    assert [type(handler).__name__ for handler in logger.handlers] == [
        "StreamHandler",
        "RotatingFileHandler",
    ]
    assert not logger.propagate

    # And messages reach the log file
    logger.info("hello bins")
    for handler in logger.handlers:
        handler.flush()
    assert "hello bins" in (tmp_path / LOG_FILE_NAME).read_text()


def test_unwritable_log_directory_falls_back_to_the_console_and_says_why_once(
    tmp_path: Path,
    restore_app_logger: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given a log directory that does not exist
    missing = tmp_path / "nope"

    # When logging is configured
    configure_logging(str(missing))

    # Then only the console handler is used
    logger = logging.getLogger(APP_LOGGER_NAME)
    assert [type(handler).__name__ for handler in logger.handlers] == ["StreamHandler"]

    # And the reason is printed once on stderr
    assert capsys.readouterr().err.count(str(missing)) == 1


def test_configuring_logging_twice_leaves_a_single_set_of_handlers(
    tmp_path: Path, restore_app_logger: None
) -> None:
    # Given logging has been configured
    configure_logging(str(tmp_path))

    # When it is configured again
    configure_logging(str(tmp_path))

    # Then the app logger has one console and one file handler
    logger = logging.getLogger(APP_LOGGER_NAME)
    assert [type(handler).__name__ for handler in logger.handlers] == [
        "StreamHandler",
        "RotatingFileHandler",
    ]


def test_importing_the_application_modules_configures_no_logging(
    tmp_path: Path,
) -> None:
    # Given a fresh interpreter whose LOG_DIR points at an empty directory
    app_dir = Path(common.logging.__file__).resolve().parent.parent
    script = (
        "import sys, logging\n"
        f"sys.path.insert(0, {str(app_dir)!r})\n"
        "import main, reminder, notify, scraper, reload, collection\n"
        "import common.settings, common.decorators\n"
        f"print(len(logging.getLogger({APP_LOGGER_NAME!r}).handlers))\n"
    )

    # When the application modules are imported
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        env={**os.environ, LOG_DIR_ENV: str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    )

    # Then the app logger has no handler and no log file was opened
    assert result.stdout.strip() == "0"
    assert list(tmp_path.iterdir()) == []


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


def test_production_rotation_limits_are_5_mb_and_5_backups(tmp_path: Path) -> None:
    # Given a writable log directory
    # When the logging config is built
    handler = build_config(str(tmp_path))["handlers"]["file"]

    # Then rotation is 5 MB per file with 5 backups
    assert handler["maxBytes"] == 5 * 1024 * 1024
    assert handler["backupCount"] == 5


def test_log_file_rolls_over_and_keeps_a_bounded_number_of_backups(
    tmp_path: Path, restore_app_logger: None
) -> None:
    # Given a config with a tiny rotation threshold
    config = build_config(str(tmp_path))
    config["handlers"]["file"]["maxBytes"] = 200
    config["handlers"]["file"]["backupCount"] = 2
    logging.config.dictConfig(config)

    # When far more than that is logged
    logger = logging.getLogger(APP_LOGGER_NAME)
    for i in range(100):
        logger.info("message number %d", i)

    # Then the log rolled over, and only the newest backups are kept
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == [LOG_FILE_NAME, f"{LOG_FILE_NAME}.1", f"{LOG_FILE_NAME}.2"]


def test_messages_are_written_to_the_log_file(
    tmp_path: Path, restore_app_logger: None
) -> None:
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


def test_console_only_when_the_log_file_cannot_be_opened(tmp_path: Path) -> None:
    # Given a log directory where the log file path cannot be opened for writing
    (tmp_path / LOG_FILE_NAME).mkdir()

    # When the logging config is built
    config = build_config(str(tmp_path))

    # Then only the console handler is configured
    assert "file" not in config["handlers"]
    assert config["loggers"][APP_LOGGER_NAME]["handlers"] == ["console"]


def test_a_warning_is_printed_when_file_logging_is_skipped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Given a log directory that does not exist
    missing = tmp_path / "nope"

    # When the logging config is built
    build_config(str(missing))

    # Then the reason is reported on stderr
    assert str(missing) in capsys.readouterr().err
