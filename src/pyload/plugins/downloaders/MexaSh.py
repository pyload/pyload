# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class MexaSh(XFSDownloader):
    __name__ = "MexaSh"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:mexa\.sh|mexashare\.com)/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Mexa.sh downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "mexa.sh"

    URL_REPLACEMENTS = [(__pattern__ + ".*", "https://mexa.sh/\g<ID>")]

    NAME_PATTERN = r">You have requested the file.+?>(?P<N>.+?)</a>"
    SIZE_PATTERN = r">\sFile Size\s: (?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)"

    WAIT_PATTERN = r'class="seconds">(\d+)<'
    DL_LIMIT_PATTERN = r"you can download this file after :.+?<a style='background.+?>(.+?)</a>"

    LINK_PATTERN = r"document.location = '(https://srv\d+.mexa.sh.+?)'"
