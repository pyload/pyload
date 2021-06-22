# -*- coding: utf-8 -*-

import re

from ..base.multi_downloader import MultiDownloader


class DebridItaliaCom(MultiDownloader):
    __name__ = "DebridItaliaCom"
    __type__ = "downloader"
    __version__ = "0.26"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.|s\d+\.)?debriditalia\.com/dl/\d+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Debriditalia.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://debriditalia.com/api.php"

    def api_request(self, method, **kwargs):
        kwargs[method] = ""
        return self.load(self.API_URL, get=kwargs)

    def handle_premium(self, pyfile):
        self.data = self.api_request(
            "generate",
            link=pyfile.url.replace("https://", "http://"),
            u=self.account.user,
            p=self.account.info["login"]["password"],
        )

        m = re.search(r"ERROR:(.*)", self.data)
        if m is None:
            self.link = self.data

        else:
            error = m.group(1).strip()

            if error in ("not_available", "not_supported"):
                self.offline()

            else:
                self.fail(error)
