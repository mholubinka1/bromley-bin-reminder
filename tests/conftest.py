import logging

import pytest
from common.logging import APP_LOGGER_NAME


@pytest.fixture
def app_log(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    # the app logger is only configured by main(), so in tests it propagates to caplog
    caplog.set_level(logging.INFO, logger=APP_LOGGER_NAME)
    return caplog
