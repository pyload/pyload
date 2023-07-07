# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class FilericeCom(XFSDownloader):
    __name__ = "FilericeCom"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filerice\.com/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filerice.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<div class="name">[^>]*>(?P<N>.+?)<'
    SIZE_PATTERN = r"<span>Size (?P<S>[\d.,]+) (?P<U>[\w^_]+)<"

    WAIT_PATTERN = r'<span class="seconds">(\d+)</span>'
    DL_LIMIT_PATTERN = r">You have to wait (.+?) till next download<"

    PLUGIN_DOMAIN = "filerice.com"
