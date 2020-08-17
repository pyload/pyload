# -*- coding: utf-8 -*-

import random

from ..base.multi_downloader import MultiDownloader


def random_with_n_digits(n):
    rand = "0."
    not_zero = 0
    for i in range(1, n + 1):
        r = random.randint(0, 9)
        if r > 0:
            not_zero += 1
        rand += str(r)

    if not_zero > 0:
        return rand
    else:
        return random_with_n_digits(n)


class MegaRapidoNet(MultiDownloader):
    __name__ = "MegaRapidoNet"
    __type__ = "downloader"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?\w+\.megarapido\.net/\?file=\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """MegaRapido.net multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Kagenoshin", "kagenoshin@gmx.ch")]

    LINK_PREMIUM_PATTERN = (
        r'<\s*?a[^>]*?title\s*?=\s*?["\'].*?download["\'][^>]*?href=["\']([^"\']+)'
    )

    ERROR_PATTERN = r'<\s*?div[^>]*?class\s*?=\s*?["\']?alert-message error.*?>([^<]*)'

    def handle_premium(self, pyfile):
        self.data = self.load(
            "http://megarapido.net/gerar.php",
            post={
                "rand": random_with_n_digits(16),
                "urllist": pyfile.url,
                "links": pyfile.url,
                "exibir": "normal",
                "usar": "premium",
                "user": self.account.get_data("sid"),
                "autoreset": "",
            },
        )

        if "desloga e loga novamente para gerar seus links" in self.data.lower():
            self.error(self._("You have logged in at another place"))

        return super().handle_premium(pyfile)
