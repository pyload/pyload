# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class HotlinkCc(SimpleDownloader):
    __name__ = "HotlinkCc"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://hotlink\.cc/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Hotlink.cc downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<i class="glyphicon glyphicon-download"></i>\s*(?P<N>.+?)<'
    SIZE_PATTERN = r"Filesize <b>(?P<S>[\d.,]+) (?P<U>[\w^_]+)<"

    WAIT_PATTERN = r'<span class="seconds yellow"><b>(\d+)<'
    DL_LIMIT_PATTERN = r"You have to wait (.+?) untill the next download"

    OFFLINE_PATTERN = r">File Not Found</"

    LINK_FREE_PATTERN = r'<a href="(https?://fs\d+.hotlink.cc/.+?)"'

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('name="F1"')
        if inputs is not None:
            self.data = self.load(pyfile.url, post=inputs)

            m = re.search(self.LINK_FREE_PATTERN, self.data)
            if m is not None:
                self.link = m.group(1)
