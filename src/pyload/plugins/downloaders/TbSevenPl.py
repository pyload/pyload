# -*- coding: utf-8 -*-

import re

from pyload.core.utils import parse

from ..base.multi_downloader import MultiDownloader


class TbSevenPl(MultiDownloader):
    __name__ = "TbSevenPl"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Tb7.pl multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<div class="name">(?P<N>.+?)<'
    SIZE_PATTERN = r'Rozmiar: <span class="type red">(?P<S>[\d.,]+) (?P<U>[\w_^]+)<'

    LINK_PATTERN = r'<a href="(.+?)" target="_blank">Pobierz</a>'

    def handle_premium(self, pyfile):
        self.data = self.load(
            "https://tb7.pl/mojekonto/sciagaj", post={"step": 1, "content": pyfile.url}
        )

        m = re.search(self.NAME_PATTERN, self.data)
        if m is not None:
            pyfile.name = m.group("N")

        m = re.search(self.SIZE_PATTERN, self.data)
        if m is not None:
            pyfile.size = parse.bytesize(m.group("S"), m.group("U"))

        self.data = self.load(
            "https://tb7.pl/mojekonto/sciagaj", post={"step": 2, "0": "on"}
        )

        if "Nieaktywne linki" in self.data:
            self.temp_offline()

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
