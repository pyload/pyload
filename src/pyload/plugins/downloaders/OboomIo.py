# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class OboomIo(SimpleDownloader):
    __name__ = "OboomIo"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://oboom\.io/file/[\d_\-\w]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Oboom.io downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_PREMIUM = True

    INFO_PATTERN = r'<t title="(?P<N>.+?)">.+?</t> <span>(?P<S>[\d.]+) (?P<U>[\w^_]+)<'

    LINK_PREMIUM_PATTERN = r'<a href="(https://\w+\.oboom\.io/download/[\d_\-\w]+)"'
