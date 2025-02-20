# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class SendCm(XFSDownloader):
    __name__ = "SendCm"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?send\.cm/(?:\w{12}|d/\w{5})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Send.cm downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "send.cm"

    LINK_PATTERN = r"(https://d\d+.download-send.com/d/.*?)[\"'<]"
    NAME_PATTERN = r"\"\[URL=https://send\.cm/\w{12}\](?P<N>.+?) -  \d+\[/URL\]\""

    DISPOSITION = False
