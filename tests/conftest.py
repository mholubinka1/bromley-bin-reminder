import logging
from collections.abc import Iterator

import pytest
from common.logging import APP_LOGGER_NAME


@pytest.fixture
def app_log(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    # the app logger propagates until logging is configured, so caplog sees it directly
    caplog.set_level(logging.INFO, logger=APP_LOGGER_NAME)
    yield caplog
