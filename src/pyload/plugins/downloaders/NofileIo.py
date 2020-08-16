# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class NofileIo(SimpleDownloader):
    __name__ = "NofileIo"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?nofile\.io/f/[\w^_]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Nofile.io downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<span id="filename">(?P<N>.+?)</span>'
    SIZE_PATTERN = (
        r"<strong>File size</strong><br/>\s*(?P<S>[\d\.,]+) (?P<U>[\w^_]+)\s*<"
    )

    LINK_PATTERN = r'data-url="(https://\w+\.nofilecdn\.io/g/.+?)"'
