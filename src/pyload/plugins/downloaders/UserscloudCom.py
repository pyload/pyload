# -*- coding: utf-8 -*-

import re

from ..base.xfs_downloader import XFSDownloader


class UserscloudCom(XFSDownloader):
    __name__ = "UserscloudCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?userscloud\.com/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Userscloud.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "userscloud.com"

    INFO_PATTERN = r'<a href="https://userscloud.com/.+?" target="_blank">(?P<N>.+?) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)</a>'
    OFFLINE_PATTERN = r"The file you are trying to download is no longer available"
    LINK_FREE_PATTERN = r'<a href="(https://\w+\.usercdn\.com.+?)"'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://userscloud.com/\g<ID>")]

    def setup(self):
        self.multi_dl = True
        self.resume_download = False
        self.chunk_limit = 1
