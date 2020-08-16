# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class FilejokerNet(XFSDownloader):
    __name__ = "FilejokerNet"
    __type__ = "downloader"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filejoker\.net/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filejoker.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "filejoker.net"

    WAIT_PATTERN = r'Please [Ww]ait (?:<span id="count" class="alert-success">)?([\w ]+?)(?:</span> seconds</p>| until the next download)'
    ERROR_PATTERN = r"Wrong Captcha"

    PREMIUM_ONLY_PATTERN = r"Free Members can download files no bigger"

    INFO_PATTERN = r'<div class="name-size"><span>(?P<N>.+?)</span> <p>\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</p></div>'
    SIZE_REPLACEMENTS = [("Kb", "KiB"), ("Mb", "MiB"), ("Gb", "GiB")]

    LINK_PATTERN = r'<div class="premium-download">\s+<a href="(.+?)"'
