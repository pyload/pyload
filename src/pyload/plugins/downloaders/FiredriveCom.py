# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FiredriveCom(DeadDownloader):
    __name__ = "FiredriveCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?(firedrive|putlocker)\.com/(mobile/)?(file|embed)/(?P<ID>\w+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Firedrive.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
