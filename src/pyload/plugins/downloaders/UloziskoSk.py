# -*- coding: utf-8 -*-
import re
import urllib.parse

from ..base.simple_downloader import SimpleDownloader


class UloziskoSk(SimpleDownloader):
    __name__ = "UloziskoSk"
    __type__ = "downloader"
    __version__ = "0.31"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?ulozisko\.sk/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Ulozisko.sk downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<div class="down1">(?P<N>.+?)</div>'
    SIZE_PATTERN = (
        r"Veľkosť súboru: <strong>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong><br />"
    )
    OFFLINE_PATTERN = r'<span class = "red">Zadaný súbor neexistuje z jedného z nasledujúcich dôvodov:</span>'

    LINK_FREE_PATTERN = r'<form name = "formular" action = "(.+?)" method = "post">'
    ID_PATTERN = r'<input type = "hidden" name = "id" value = "(.+?)" />'
    CAPTCHA_PATTERN = r'<img src="(/obrazky/obrazky\.php\?fid=.+?)" alt="" />'
    IMG_PATTERN = (
        r'<strong>PRE ZVÄČŠENIE KLIKNITE NA OBRÁZOK</strong><br /><a href = "(.+?)">'
    )

    def process(self, pyfile):
        self.data = self.load(pyfile.url)
        self.get_file_info()

        m = re.search(self.IMG_PATTERN, self.data)
        if m is not None:
            self.link = "http://ulozisko.sk" + m.group(1)
        else:
            self.handle_free(pyfile)

    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(self._("LINK_FREE_PATTERN not found"))
        parsed_url = "http://www.ulozisko.sk" + m.group(1)

        m = re.search(self.ID_PATTERN, self.data)
        if m is None:
            self.error(self._("ID_PATTERN not found"))
        id = m.group(1)

        self.log_debug("URL:" + parsed_url + " ID:" + id)

        m = re.search(self.CAPTCHA_PATTERN, self.data)
        if m is None:
            self.error(self._("CAPTCHA_PATTERN not found"))

        captcha_url = urllib.parse.urljoin("http://www.ulozisko.sk/", m.group(1))
        captcha = self.captcha.decrypt(captcha_url, cookies=True)

        self.log_debug("CAPTCHA_URL:" + captcha_url + " CAPTCHA:" + captcha)

        self.download(
            parsed_url,
            post={
                "antispam": captcha,
                "id": id,
                "name": pyfile.name,
                "but": "++++STIAHNI+S%DABOR++++",
            },
        )
