# -*- coding: utf-8 -*-

import re

from ..base.xfs_downloader import XFSDownloader


class NosuploadCom(XFSDownloader):
    __name__ = "NosuploadCom"
    __type__ = "downloader"
    __version__ = "0.38"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?nosupload\.com/\?d=\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Nosupload.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("igel", "igelkun@myopera.com")]

    PLUGIN_DOMAIN = "nosupload.com"

    SIZE_PATTERN = r"<p><strong>Size:</strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)</p>"
    LINK_PATTERN = r'<a class="select" href="(http://.+?)">Download</a>'

    WAIT_PATTERN = r"Please wait.*?>(\d+)</span>"

    def get_download_link(self):
        #: Stage1: press the "Free Download" button
        data = self._post_parameters()
        self.data = self.load(self.pyfile.url, post=data)

        #: Stage2: wait some time and press the "Download File" button
        data = self._post_parameters()
        wait_time = re.search(self.WAIT_PATTERN, self.data, re.M | re.S).group(1)
        self.log_debug(f"Hoster told us to wait {wait_time} seconds")
        self.wait(wait_time)
        self.data = self.load(self.pyfile.url, post=data)

        #: Stage3: get the download link
        return re.search(self.LINK_PATTERN, self.data, re.S).group(1)
