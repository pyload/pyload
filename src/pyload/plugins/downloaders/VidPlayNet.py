# -*- coding: utf-8 -*-

#
# Test links:
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://vidplay.net/38lkev0h3jv0

from ..base.xfs_downloader import XFSDownloader


class VidPlayNet(XFSDownloader):
    __name__ = "VidPlayNet"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?vidplay\.net/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """VidPlay.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]

    PLUGIN_DOMAIN = "vidplay.net"

    NAME_PATTERN = r"<b>Password:</b></div>\s*<h[1-6]>(?P<N>.+?)</h[1-6]>"
