from common.settings import ApplicationSettings
from support import yaml_settings as _yaml_settings


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


def test_ntfy_topic_is_stripped_of_surrounding_whitespace() -> None:
    # Given an ntfy block whose topic has surrounding whitespace
    yaml_settings = _yaml_settings(ntfy={"topic": "  my-bins "})

    # When the settings are loaded
    settings = ApplicationSettings(yaml_settings)

    # Then the topic is trimmed
    assert settings.ntfy is not None
    assert settings.ntfy.topic == "my-bins"


def test_ntfy_topic_written_as_a_number_in_yaml_is_accepted() -> None:
    # Given an ntfy block whose topic YAML parses as a number
    yaml_settings = _yaml_settings(ntfy={"topic": 12345})

    # When the settings are loaded
    settings = ApplicationSettings(yaml_settings)

    # Then the topic is kept as text
    assert settings.ntfy is not None
    assert settings.ntfy.topic == "12345"


def test_ntfy_uses_the_default_server_when_the_server_is_blank() -> None:
    # Given an ntfy block with a topic and a blank server
    yaml_settings = _yaml_settings(ntfy={"server": " ", "topic": "my-bins"})

    # When the settings are loaded
    settings = ApplicationSettings(yaml_settings)

    # Then the default ntfy server is used
    assert settings.ntfy is not None
    assert settings.ntfy.server == "https://ntfy.sh"


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
