# -*- coding: utf-8 -*-


from ..base.xfs_downloader import XFSDownloader


class SuprafilesMe(XFSDownloader):
    __name__ = "SuprafilesMe"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:suprafiles\.me|sfiles\.org)/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Suprafiles.me downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "suprafiles.me"

    URL_REPLACEMENTS = [((__pattern__ + ".*", r"http://sfiles.org/\g<ID>"))]

    NAME_PATTERN = r'<span class="dfilename">Download File (?P<N>.+?)</span>'
    SIZE_PATTERN = (
        r'<span class="statd">Size</span>\s*<span><b>(?P<S>[\d.,]+) (?P<U>[\w^_]+?)<'
    )
    OFFLINE_PATTERN = r">File Not Found"
    ERROR_PATTERN = r'(?:class=["\']err["\'].*?>|>Error</td>|>\(ERROR:)(?:\s*<.+?>\s*)*(.+?)(?:["\']|<|\))'

    LINK_PATTERN = r'<a href="(http://fs\d+\.suprafiles\.me.+?)"'

    RECAPTCHA_PATTERN = (
        r'<div class="g-recaptcha" data-sitekey="((?:[\w\-]|%[0-9a-fA-F]{2})+)"'
    )
