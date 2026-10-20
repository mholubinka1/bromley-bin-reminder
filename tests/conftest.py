import logging
from collections.abc import Iterator

import pytest
from common.logging import APP_LOGGER_NAME


@pytest.fixture
def app_log(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    # the app logger does not propagate, so caplog only sees it through this handler
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger=APP_LOGGER_NAME)
    yield caplog
    app_logger.removeHandler(caplog.handler)
