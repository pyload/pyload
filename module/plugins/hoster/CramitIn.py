# -*- coding: utf-8 -*-

from ..internal.XFSHoster import XFSHoster


class CramitIn(XFSHoster):
    __name__ = "CramitIn"
    __type__ = "hoster"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?cramit\.in/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Cramit.in hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    PLUGIN_DOMAIN = "cramit.in"

    INFO_PATTERN = r'<span class=t2>\s*(?P<N>.*?)</span>.*?<small>\s*\((?P<S>.*?)\)'
    LINK_PATTERN = r'href="(http://cramit\.in/file_download/.*?)"'
