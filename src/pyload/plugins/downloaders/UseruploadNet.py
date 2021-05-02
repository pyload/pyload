# -*- coding: utf-8 -*-

import re

from ..base.xfs_downloader import XFSDownloader


class UseruploadNet(XFSDownloader):
    __name__ = "UseruploadNet"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?userupload\.net/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Userupload.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("OzzieIsaacs", "ozzie.fernandez.isaacs@gmail.com")]

    PLUGIN_DOMAIN = "userupload.net"

    NAME_PATTERN = r"<title>Download (?P<N>.+?)</title>"
    SIZE_PATTERN = r"<span>File Size : (?P<S>[\d.,]+) (?P<U>[\w^_]+)</span>"

    LINK_PATTERN = r'<a href="(.+?)" type="button" class="btn btn-primary btn-block mb-4">'

    def handle_free(self, pyfile):
        self.check_errors()

        self.data = self.load(
            pyfile.url,
            post=self._post_parameters(),
            ref=self.pyfile.url,
            redirect=False,
        )

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
            pyfile.name = self.link.split("/")[-1]
