# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class WorldbytezCom(XFSDownloader):
    __name__ = "WorldbytezCom"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?worldbytez\.com/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Worldbytez.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "worldbytez.com"

    PLUGIN_URL = "https://worldbytez.com/download"

    WAIT_PATTERN = r'<span class="seconds">(\d+)</span>'
    SIZE_LIMIT_PATTERN = r'Upgrade your account to download bigger files'

    LINK_PATTERN = r'<a href="(https://[^/]+/d/[^"]+)"'
