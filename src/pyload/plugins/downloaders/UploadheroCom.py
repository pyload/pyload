# -*- coding: utf-8 -*-

import re
import urllib.parse
from datetime import timedelta

from ..base.simple_downloader import SimpleDownloader

#
# Test links:
# http://uploadhero.co/dl/wQBRAVSM


class UploadheroCom(SimpleDownloader):
    __name__ = "UploadheroCom"
    __type__ = "downloader"
    __version__ = "0.23"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?uploadhero\.com?/dl/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """UploadHero.co plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mcmyst", "mcmyst@hotmail.fr"), ("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<div class="nom_de_fichier">(?P<N>.+?)<'
    SIZE_PATTERN = r">Filesize: </span><strong>(?P<S>[\d.,]+) (?P<U>[\w^_]+)"
    OFFLINE_PATTERN = r'<p class="titre_dl_2">'

    COOKIES = [("uploadhero.co", "lang", "en")]

    IP_BLOCKED_PATTERN = r'href="(/lightbox_block_download\.php\?min=.+?)"'
    IP_WAIT_PATTERN = (
        r'<span id="minutes">(\d+)</span>.*\s*<span id="seconds">(\d+)</span>'
    )

    CAPTCHA_PATTERN = r'"(/captchadl\.php\?\w+)"'

    LINK_FREE_PATTERN = (
        r'var magicomfg = \'<a href="(.+?)"|"(http://storage\d+\.uploadhero\.co.+?)"'
    )
    LINK_PREMIUM_PATTERN = r'<a href="(.+?)" id="downloadnow"'

    def handle_free(self, pyfile):
        m = re.search(self.CAPTCHA_PATTERN, self.data)
        if m is None:
            self.error(self._("Captcha not found"))

        captcha = self.captcha.decrypt(
            urllib.parse.urljoin("http://uploadhero.co/", m.group(1))
        )

        self.data = self.load(pyfile.url, get={"code": captcha})

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1) or m.group(2)
            self.wait(50)

    def check_errors(self):
        m = re.search(self.IP_BLOCKED_PATTERN, self.data)
        if m is not None:
            self.data = self.load(
                urllib.parse.urljoin("http://uploadhero.co/", m.group(1))
            )

            m = re.search(self.IP_WAIT_PATTERN, self.data)
            wait_time = (
                (timedelta(minutes=int(m.group(1))).seconds + int(m.group(2)))
                if m
                else timedelta(minutes=5).seconds
            )
            self.wait(wait_time, True)
            self.retry()

        return SimpleDownloader.check_errors(self)
