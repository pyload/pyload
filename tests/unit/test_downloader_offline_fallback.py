from unittest.mock import MagicMock

import pytest

from pyload.core.network.exceptions import Fail, Retry
from pyload.plugins.downloaders.RapidgatorNet import RapidgatorNet


def _make_downloader(failure):
    downloader = object.__new__(RapidgatorNet)
    downloader.pyload = MagicMock()
    downloader.pyfile = MagicMock()
    downloader.pyfile.error = ""
    downloader.config = MagicMock()
    downloader.config.get.return_value = True
    downloader.premium = True
    downloader.no_fallback = False
    downloader.restart_free = False
    downloader._ = lambda text: text
    downloader.log_info = MagicMock()
    downloader.log_warning = MagicMock()
    downloader._initialize = MagicMock()
    downloader._setup = MagicMock()
    downloader._finalize = MagicMock()
    downloader.check_duplicates = MagicMock()
    downloader.process = MagicMock(side_effect=lambda pyfile: failure(downloader))
    return downloader


def test_premium_offline_does_not_fall_back_to_free():
    downloader = _make_downloader(lambda d: d.offline())

    with pytest.raises(Fail) as exc_info:
        downloader._process(MagicMock())

    assert exc_info.value.args[0] == "offline"
    assert downloader.restart_free is False


def test_premium_generic_failure_falls_back_to_free():
    downloader = _make_downloader(lambda d: d.fail("some error"))

    with pytest.raises(Retry):
        downloader._process(MagicMock())

    assert downloader.restart_free is True
