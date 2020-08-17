# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class FilerioCom(XFSDownloader):
    __name__ = "FilerioCom"
    __type__ = "downloader"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?(filerio\.(in|com)|filekeen\.com)/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """FileRio.in downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    PLUGIN_DOMAIN = "filerio.com"

    URL_REPLACEMENTS = [(r"filekeen\.com", "filerio.in")]

    OFFLINE_PATTERN = r">&quot;File Not Found|File has been removed"
