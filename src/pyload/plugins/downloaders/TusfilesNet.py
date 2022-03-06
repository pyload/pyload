# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class TusfilesNet(XFSDownloader):
    __name__ = "TusfilesNet"
    __type__ = "downloader"
    __version__ = "0.20"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?tusfiles\.(?:net|com)/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Tusfiles.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("guidobelix", "guidobelix@hotmail.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    PLUGIN_DOMAIN = "tusfiles.com"
    URL_REPLACEMENTS = [(r"tusfiles\.net", "tusfiles.com")]

    NAME_PATTERN = r'fa-file-o"></i>\s*(?P<N>.+) <'
    SIZE_PATTERN = r"<b>\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</b></small>"

    OFFLINE_PATTERN = r"The file you are trying to download is no longer available!"

    def setup(self):
        self.resume_download = True
        self.chunk_limit = 1
        self.multi_dl = True
        self.limit_dl = 2
