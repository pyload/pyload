# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class SendspaceCom(SimpleDownloader):
    __name__ = "SendspaceCom"
    __type__ = "downloader"
    __version__ = "0.23"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?sendspace\.com/file/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Sendspace.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<h2 class="bgray">\s*<(?:b|strong)>(?P<N>.+?)</'
    SIZE_PATTERN = r'<div class="file_description reverse margin_center">\s*<b>File Size:</b>\s*(?P<S>[\d.,]+)(?P<U>[\w^_]+)\s*</div>'
    OFFLINE_PATTERN = r'<div class="msg error" style="cursor: default">Sorry, the file you requested is not available.</div>'

    LINK_FREE_PATTERN = (
        r'<a id="download_button" class="download_page_button button1" href="(.+?)"'
    )

    CAPTCHA_PATTERN = r'<td><img src="(/captchas/captcha\.php?captcha=(.+?))"></td>'
    USER_CAPTCHA_PATTERN = r'<td><img src="/captchas/captcha\.php?user=(.+?))"></td>'

    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

        else:
            m = re.search(self.CAPTCHA_PATTERN, self.data)
            if m is None:
                params = {"download": "Regular Download"}
            else:
                captcha_url1 = "http://www.sendspace.com/" + m.group(1)
                m = re.search(self.USER_CAPTCHA_PATTERN, self.data)
                captcha_url2 = "http://www.sendspace.com/" + m.group(1)
                params = {
                    "captcha_hash": m.group(2),
                    "captcha_submit": "Verify",
                    "captcha_answer": self.captcha.decrypt(captcha_url1)
                    + " "
                    + self.captcha.decrypt(captcha_url2),
                }

            self.log_debug(params)

            self.data = self.load(pyfile.url, post=params)

            m = re.search(self.LINK_FREE_PATTERN, self.data)
            if m is None:
                self.retry_captcha()
            else:
                self.link = m.group(1)
