# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class DownupSpace(XFSDownloader):
    __name__ = "DownupSpace"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?downup\.space/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Downup.space downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "downup.space"
    WAIT_PATTERN = r"var seconds = (\d+);"
    DL_LIMIT_PATTERN = r"You have to wait ([\w ,]+) till next download"
    LINK_PATTERN = r'<a href="(https://s\d+\.downup\.space.+?)"'

