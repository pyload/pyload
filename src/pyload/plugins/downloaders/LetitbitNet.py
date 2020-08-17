# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class LetitbitNet(DeadDownloader):
    __name__ = "LetitbitNet"
    __type__ = "downloader"
    __version__ = "0.39"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(letitbit|shareflare)\.net/download/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Letitbit.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"), ("z00nx", "z00nx0@gmail.com")]
