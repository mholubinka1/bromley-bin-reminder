from typing import Any

from common.settings import ApplicationSettings


def _yaml_settings(**extra: Any) -> dict[str, Any]:
    return {
        "remind": {
            "url": "https://example.com/collections",
            "email_addresses": ["a@example.com"],
            "time": "18:00",
        },
        "smtp": {
            "username": "a",
            "password": "b",
            "server": "s",
            "port": 587,
        },
        **extra,
    }


def test_ntfy_is_not_configured_when_the_yaml_has_no_ntfy_block() -> None:
    # Given config yaml with no ntfy block
    yaml_settings = _yaml_settings()

    # When the settings are loaded
    settings = ApplicationSettings(yaml_settings)

    # Then ntfy is not configured
    assert settings.ntfy is None


def test_ntfy_is_not_configured_when_the_topic_is_blank() -> None:
    # Given config yaml with an ntfy block whose topic is blank
    yaml_settings = _yaml_settings(
        ntfy={"server": "https://ntfy.example.com", "topic": " "}
    )

    # When the settings are loaded
    settings = ApplicationSettings(yaml_settings)

    # Then ntfy is not configured
    assert settings.ntfy is None


def test_ntfy_uses_the_public_server_when_none_is_configured() -> None:
    # Given an ntfy block with a topic and no server
    yaml_settings = _yaml_settings(ntfy={"topic": "my-bins"})

    # When the settings are loaded
    settings = ApplicationSettings(yaml_settings)

    # Then the default ntfy server is used and the topic is preserved
    assert settings.ntfy is not None
    assert settings.ntfy.server == "https://ntfy.sh"
    assert settings.ntfy.topic == "my-bins"


def test_ntfy_keeps_a_custom_server() -> None:
    # Given an ntfy block with a topic and a custom server
    yaml_settings = _yaml_settings(
        ntfy={"server": "https://ntfy.example.com", "topic": "my-bins"}
    )

    # When the settings are loaded
    settings = ApplicationSettings(yaml_settings)

    # Then the custom server is preserved
    assert settings.ntfy is not None
    assert settings.ntfy.server == "https://ntfy.example.com"
