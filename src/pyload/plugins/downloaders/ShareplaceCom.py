# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.simple_downloader import SimpleDownloader


class ShareplaceCom(SimpleDownloader):
    __name__ = "ShareplaceCom"
    __type__ = "downloader"
    __version__ = "0.19"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?shareplace\.(com|org)/\?\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Shareplace.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ACCakut", None), ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r"Filename:</font></b>\s*(?P<N>.+?)<b><br>"
    SIZE_PATTERN = r"Filesize:</font></b>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)<b><br>"

    TEMP_OFFLINE_PATTERN = r"^unmatchable$"
    OFFLINE_PATTERN = r"Your requested file is not found"

    WAIT_PATTERN = r"var zzipitime = (\d+);"

    def handle_free(self, pyfile):
        response = self.captcha.decrypt("http://shareplace.com/captcha.php")

        self.data = self.load(pyfile.url, post={"captchacode": response})
        if "Captcha number error or expired" in self.data:
            self.retry_captcha()

        self.captcha.correct()
        self.check_errors()

        m = re.search(r"var beer = '(.+?)'", self.data)
        if m is not None:
            self.link = urllib.parse.unquote(
                urllib.parse.unquote(
                    m.group(1).replace("vvvvvvvvv", "").replace("lllllllll", "")
                ).replace("teletubbies", "")
            )[13:]
