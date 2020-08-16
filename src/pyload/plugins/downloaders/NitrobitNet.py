# -*- coding: utf-8 -*-
import re
import time

import pycurl
from pyload.core.utils import format

from ..base.simple_downloader import SimpleDownloader


class NitrobitNet(SimpleDownloader):
    __name__ = "NitrobitNet"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?nitrobit.net/(?:view|watch)/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Nitrobit.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_PREMIUM = True
    URL_REPLACEMENTS = [(__pattern__ + ".*", r"http://www.nitrobit.net/view/\g<ID>")]

    NAME_PATTERN = r'<b>שם הקובץ: </b><span title="(?P<N>.+?)"'
    SIZE_PATTERN = r'<b>גודל הקובץ: </b><span dir="ltr" style="text-align: left;">(?P<S>[\d.,]+) (?P<U>[\w^_]+)</span>'

    DL_LIMIT_PATTERN = (
        r"daily downloadlimit reached|הורדת קובץ זה תעבור על המכסה היומית"
    )
    LINK_PREMIUM_PATTERN = r'id="download" href="(.+?)"'

    def handle_premium(self, pyfile):
        current_millis = int(time.time() * 1000)

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.data = self.load(
            "http://www.nitrobit.net/ajax/unlock.php",
            get={
                "password": self.account.info["login"]["password"],
                "file": self.info["pattern"]["ID"],
                "keep": "false",
                "_": current_millis,
            },
        )

        m = re.search(r'id="unlockedTick".+?alt="(\d+)"', self.data)
        if m is not None:
            validuntil = time.time() + float(m.group(1))
            self.log_info(
                self._("Account valid until {}").format(
                    time.strftime("%d/%m/%Y"), time.gmtime(validuntil)
                )
            )

        m = re.search(r'id="dailyVolume" value="(\d+)?/(\d+)"', self.data)
        if m is not None:
            trafficleft = int(m.group(2)) - int((m.group(1) or "0"))
            self.log_info(
                self._("Daily traffic left {}").format(format.size(trafficleft))
            )

        m = re.search(self.LINK_PREMIUM_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
