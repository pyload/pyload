# -*- coding: utf-8 -*-

import re
from datetime import timedelta

from pyload.core.network.request_factory import get_url

from ..base.hoster import parse_file_info
from ..base.simple_downloader import SimpleDownloader


def get_info(urls):
    for url in urls:
        h = get_url(url, just_header=True)
        m = re.search(r"Location: (.+)\r\n", h)

        if m and not re.match(
            m.group(1), FilefactoryCom.__pattern__
        ):  #: : It's a direct link! Skipping
            yield (url, 0, 7, url)
        else:
            #: It's a standard html page
            yield parse_file_info(FilefactoryCom, url, get_url(url))


class FilefactoryCom(SimpleDownloader):
    __name__ = "FilefactoryCom"
    __type__ = "downloader"
    __version__ = "0.64"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filefactory\.com/(file|trafficshare/\w+)/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filefactory.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    INFO_PATTERN = r'<div id="file_name"[^>]*>\s*<h2>(?P<N>[^<]+)</h2>\s*<div id="file_info">\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+) uploaded'
    OFFLINE_PATTERN = (
        r"<h2>File Removed</h2>|This file is no longer available|Invalid Download Link"
    )

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'"([^"]+filefactory\.com/get.+?)"'

    WAIT_PATTERN = r'<div id="countdown_clock" data-delay="(\d+)">'
    PREMIUM_ONLY_PATTERN = r">Premium Account Required"

    COOKIES = [("filefactory.com", "locale", "en_US.utf-8")]

    def handle_free(self, pyfile):
        if "Currently only Premium Members can download files larger than" in self.data:
            self.fail(self._("File too large for free download"))
        elif "All free download slots on this server are currently in use" in self.data:
            self.retry(
                50, timedelta(minutes=15).seconds, self._("All free slots are busy")
            )

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            return

        self.link = m.group(1)

        m = re.search(self.WAIT_PATTERN, self.data)
        if m is not None:
            self.wait(m.group(1))

    def check_download(self):
        check = self.scan_download(
            {
                "multiple": "You are currently downloading too many files at once.",
                "error": '<div id="errorMessage">',
            }
        )

        if check == "multiple":
            self.log_debug("Parallel downloads detected; waiting 15 minutes")
            self.retry(
                wait=timedelta(minutes=15).seconds, msg=self._("Parallel downloads")
            )

        elif check == "error":
            self.error(self._("Unknown error"))

        return SimpleDownloader.check_download(self)
