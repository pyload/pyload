# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class FilerioCom(XFSDownloader):
    __name__ = "FilerioCom"
    __type__ = "downloader"
    __version__ = "0.14"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filerio\.(in|com)/\w{12}"
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

    PLUGIN_DOMAIN = "filerio.in"

    URL_REPLACEMENTS = [("http://", "https://")]

    OFFLINE_PATTERN = r">&quot;File Not Found|File has been removed"

    LINK_PATTERN = r'<a href="(.+?)" class="btn btn-primary btn-block">'
