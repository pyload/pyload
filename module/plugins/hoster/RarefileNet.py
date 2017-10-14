# -*- coding: utf-8 -*-


from ..internal.XFSHoster import XFSHoster


class RarefileNet(XFSHoster):
    __name__ = "RarefileNet"
    __type__ = "hoster"
    __version__ = "0.15"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?rarefile\.net/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Rarefile.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    PLUGIN_DOMAIN = "rarefile.net"

    LINK_PATTERN = r'<a href="(.+?)">\1</a>'
