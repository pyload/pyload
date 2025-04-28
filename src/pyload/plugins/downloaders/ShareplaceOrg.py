# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class ShareplaceOrg(SimpleDownloader):
    __name__ = "ShareplaceOrg"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?shareplace\.org/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Shareplace.org downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://shareplace.org/\g<ID>")]

    INFO_PATTERN = r"<strong>\s*(?P<N>.+?) \((?P<S>[\d.]+) (?P<U>[\w^_]+)\)\s*</strong>\s*<p>Choose free or premium download</p>"
    WAIT_PATTERN = r"\$\('\.download-timer-seconds'\)\.html\((\d+)\);"

    LINK_FREE_PATTERN = r"href='(https://shareplace.org/\w+\?pt=[^']+)'"
