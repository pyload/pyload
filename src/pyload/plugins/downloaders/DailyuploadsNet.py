# -*- coding: utf-8 -*-

import re

from ..base.xfs_downloader import XFSDownloader


class DailyuploadsNet(XFSDownloader):
    __name__ = "DailyuploadsNet"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?dailyuploads\.net/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Dailyuploads.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "dailyuploads.net"

    NAME_PATTERN = r'<textarea readonly="" .+?>https://dailyuploads.net/\w+?/(?P<N>.+?)<'
    SIZE_PATTERN = r"<small>\((?P<S>[\d.,]+) (?P<U>bytes)\)</small>"

    LINK_PATTERN = r'<a href="(https?://cdn\d+.dailyuploads.net/.+?)">'

    def setup(self):
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = 1

