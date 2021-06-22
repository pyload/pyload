# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class LetsuploadCc(SimpleDownloader):
    __name__ = "LetsuploadCc"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?letsupload\.cc/(?P<ID>\w{10})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Letsupload.cc downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://letsupload.cc/\g<ID>")]

    NAME_PATTERN = r'<h1 class="text-center text-wordwrap">(?P<N>.+?)</h1>'
    SIZE_PATTERN = r">Download\s*\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</a>"

    LINK_FREE_PATTERN = r'href="(https://cdn-\d+\.letsupload\.cc/.+?)"'
