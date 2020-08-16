# -*- coding: utf-8 -*-

#
# Test links:
# http://data.hu/get/6381232/random.bin


from ..base.simple_downloader import SimpleDownloader


class DataHu(SimpleDownloader):
    __name__ = "DataHu"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?data\.hu/get/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Data.hu downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("crash", None), ("stickell", "l.stickell@yahoo.it")]

    INFO_PATTERN = r"<title>(?P<N>.*) \((?P<S>[^)]+)\) let\xf6lt\xe9se</title>"
    OFFLINE_PATTERN = r"Az adott f\xe1jl nem l\xe9tezik"
    LINK_FREE_PATTERN = r'<div class="download_box_button"><a href="(.+?)">'

    def setup(self):
        self.resume_download = True
        self.multi_dl = self.premium
