import logging
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml
from common.settings import load_settings, parse_settings
from support import yaml_settings as _yaml_settings


def test_a_valid_settings_file_is_loaded(tmp_path: Path) -> None:
    # Given a config file holding valid settings
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.safe_dump(_yaml_settings()))

    # When the settings are loaded from it
    settings = load_settings(str(config_file))

    # Then the valid settings are returned
    assert settings.wasteworks_url == "https://example.com/collections"
    assert settings.smtp.server == "smtp.example.com"


def test_a_file_that_fails_validation_is_not_reported_as_loaded(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Given a config file whose settings are invalid
    invalid = _yaml_settings()
    invalid["remind"]["url"] = ""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.safe_dump(invalid))

    # When the settings are loaded
    with caplog.at_level(logging.INFO), pytest.raises(RuntimeError):
        load_settings(str(config_file))

    # Then no success is logged
    assert "Successfully loaded settings" not in caplog.text


def test_a_missing_settings_file_is_reported_with_its_path(tmp_path: Path) -> None:
    # Given a config path with no file at it
    config_file = tmp_path / "missing.yaml"

    # When the settings are loaded, then loading fails naming the path
    with pytest.raises(RuntimeError, match=str(config_file)):
        load_settings(str(config_file))


def test_a_malformed_settings_file_is_reported_with_its_path(tmp_path: Path) -> None:
    # Given a config file that is not valid YAML
    config_file = tmp_path / "config.yaml"
    config_file.write_text("remind: [unclosed")

    # When the settings are loaded, then loading fails naming the path
    with pytest.raises(RuntimeError, match=str(config_file)):
        load_settings(str(config_file))


def test_a_valid_timezone_is_resolved_once_and_its_name_kept() -> None:
    # Given config yaml with a valid timezone
    config = _yaml_settings()
    config["remind"]["tz"] = "America/New_York"

    # When the settings are parsed
    settings = parse_settings(config)

    # Then the timezone is resolved and its name is kept for the scheduler
    assert settings.timezone == ZoneInfo("America/New_York")
    assert settings.remind.tz == "America/New_York"


def test_a_blank_poll_time_falls_back_to_the_default_with_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given config yaml with a blank poll time
    config = _yaml_settings()
    config["remind"]["time"] = " "

    # When the settings are parsed
    with caplog.at_level(logging.WARNING):
        settings = parse_settings(config)

    # Then the default poll time is used and the resident is warned
    assert settings.remind.time == "18:00"
    assert "Custom daily poll time not provided, using default: 18:00" in caplog.text


def test_a_blank_timezone_falls_back_to_london_with_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given config yaml with no timezone
    config = _yaml_settings()

    # When the settings are parsed
    with caplog.at_level(logging.WARNING):
        settings = parse_settings(config)

    # Then Europe/London is used and the resident is warned
    assert settings.remind.tz == "Europe/London"
    assert settings.timezone == ZoneInfo("Europe/London")
    assert "Custom timezone not provided, using default: Europe/London" in caplog.text


@pytest.mark.parametrize(
    "name",
    ["Mars/Olympus_Mons", "Europe", "../x", "posixrules", "Factory", "europe/london"],
)
def test_an_unrecognised_timezone_falls_back_to_london_with_a_warning(
    caplog: pytest.LogCaptureFixture, name: str
) -> None:
    # Given config yaml with a timezone that is not a zone name
    config = _yaml_settings()
    config["remind"]["tz"] = name

    # When the settings are parsed
    with caplog.at_level(logging.WARNING):
        settings = parse_settings(config)

    # Then Europe/London is used and the resident is warned
    assert settings.remind.tz == "Europe/London"
    assert settings.timezone == ZoneInfo("Europe/London")
    assert f"Unrecognised timezone {name}, using default: Europe/London" in caplog.text


def test_a_blank_wasteworks_url_is_rejected() -> None:
    # Given config yaml with a blank WasteWorks URL
    config = _yaml_settings()
    config["remind"]["url"] = " "

    # When the settings are parsed, then they are rejected
    with pytest.raises(RuntimeError, match="A valid wasteworks URL must be provided."):
        parse_settings(config)


def test_a_blank_smtp_username_is_rejected() -> None:
    # Given config yaml with a blank SMTP username
    config = _yaml_settings()
    config["smtp"]["username"] = ""

    # When the settings are parsed, then they are rejected
    with pytest.raises(
        RuntimeError, match="A valid sender e-mail address must be provided."
    ):
        parse_settings(config)


def test_a_blank_smtp_server_is_rejected() -> None:
    # Given config yaml with a blank SMTP server
    config = _yaml_settings()
    config["smtp"]["server"] = " "

    # When the settings are parsed, then they are rejected
    with pytest.raises(
        RuntimeError, match="SMTP server and port configurations must be provided."
    ):
        parse_settings(config)


def test_a_missing_smtp_port_is_rejected() -> None:
    # Given config yaml with no SMTP port value
    config = _yaml_settings()
    config["smtp"]["port"] = None

    # When the settings are parsed, then they are rejected
    with pytest.raises(
        RuntimeError, match="SMTP server and port configurations must be provided."
    ):
        parse_settings(config)


def test_a_missing_required_key_is_rejected() -> None:
    # Given config yaml with no smtp block
    config = _yaml_settings()
    del config["smtp"]

    # When the settings are parsed, then they are rejected
    with pytest.raises(KeyError):
        parse_settings(config)


def test_ntfy_is_not_configured_when_the_yaml_has_no_ntfy_block() -> None:
    # Given config yaml with no ntfy block
    config = _yaml_settings()

    # When the settings are loaded
    settings = parse_settings(config)

    # Then ntfy is not configured
    assert settings.ntfy is None


def test_ntfy_is_not_configured_when_the_topic_is_blank() -> None:
    # Given config yaml with an ntfy block whose topic is blank
    config = _yaml_settings(ntfy={"server": "https://ntfy.example.com", "topic": " "})

    # When the settings are loaded
    settings = parse_settings(config)

    # Then ntfy is not configured
    assert settings.ntfy is None


def test_ntfy_uses_the_public_server_when_none_is_configured() -> None:
    # Given an ntfy block with a topic and no server
    config = _yaml_settings(ntfy={"topic": "my-bins"})

    # When the settings are loaded
    settings = parse_settings(config)

    # Then the default ntfy server is used and the topic is preserved
    assert settings.ntfy is not None
    assert settings.ntfy.server == "https://ntfy.sh"
    assert settings.ntfy.topic == "my-bins"


def test_ntfy_topic_is_stripped_of_surrounding_whitespace() -> None:
    # Given an ntfy block whose topic has surrounding whitespace
    config = _yaml_settings(ntfy={"topic": "  my-bins "})

    # When the settings are loaded
    settings = parse_settings(config)

    # Then the topic is trimmed
    assert settings.ntfy is not None
    assert settings.ntfy.topic == "my-bins"


def test_ntfy_topic_written_as_a_number_in_yaml_is_accepted() -> None:
    # Given an ntfy block whose topic YAML parses as a number
    config = _yaml_settings(ntfy={"topic": 12345})

    # When the settings are loaded
    settings = parse_settings(config)

    # Then the topic is kept as text
    assert settings.ntfy is not None
    assert settings.ntfy.topic == "12345"


def test_ntfy_uses_the_default_server_when_the_server_is_blank() -> None:
    # Given an ntfy block with a topic and a blank server
    config = _yaml_settings(ntfy={"server": " ", "topic": "my-bins"})

    # When the settings are loaded
    settings = parse_settings(config)

    # Then the default ntfy server is used
    assert settings.ntfy is not None
    assert settings.ntfy.server == "https://ntfy.sh"


def test_ntfy_server_is_stripped_of_surrounding_whitespace() -> None:
    # Given an ntfy block whose server has surrounding whitespace
    config = _yaml_settings(
        ntfy={"server": " https://ntfy.example.com ", "topic": "my-bins"}
    )

    # When the settings are loaded
    settings = parse_settings(config)

    # Then the server is trimmed
    assert settings.ntfy is not None
    assert settings.ntfy.server == "https://ntfy.example.com"


def test_ntfy_keeps_a_custom_server() -> None:
    # Given an ntfy block with a topic and a custom server
    config = _yaml_settings(
        ntfy={"server": "https://ntfy.example.com", "topic": "my-bins"}
    )

    # When the settings are loaded
    settings = parse_settings(config)

    # Then the custom server is preserved
    assert settings.ntfy is not None
    assert settings.ntfy.server == "https://ntfy.example.com"
