# -*- coding: utf-8 -*-
import re

import pycurl

from ..base.simple_downloader import SimpleDownloader


class WrzucTo(SimpleDownloader):
    __name__ = "WrzucTo"
    __type__ = "downloader"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?wrzuc\.to/(\w+(\.wt|\.html)|(\w+/?linki/\w+))"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Wrzuc.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'id="file_info">\s*<strong>(?P<N>.*?)</strong>'
    SIZE_PATTERN = r'class="info">\s*<tr>\s*<td>(?P<S>.*?)</td>'

    COOKIES = [("wrzuc.to", "language", "en")]

    def setup(self):
        self.multi_dl = True

    def handle_free(self, pyfile):
        data = dict(re.findall(r'(md5|file): "(.*?)"', self.data))
        if len(data) != 2:
            self.error(self._("No file ID"))

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.last_url = pyfile.url
        self.load("http://www.wrzuc.to/ajax/server/prepair", post={"md5": data["md5"]})

        self.req.http.last_url = pyfile.url
        self.data = self.load(
            "http://www.wrzuc.to/ajax/server/download_link", post={"file": data["file"]}
        )

        data.update(re.findall(r'"(download_link|server_id)":"(.*?)"', self.data))
        if len(data) != 4:
            self.error(self._("No download URL"))

        self.link = "http://{}.wrzuc.to/pobierz/{}".format(
            data["server_id"], data["download_link"]
        )
