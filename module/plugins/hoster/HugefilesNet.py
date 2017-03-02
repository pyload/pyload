# -*- coding: utf-8 -*-


from ..internal.XFSHoster import XFSHoster


class HugefilesNet(XFSHoster):
    __name__ = "HugefilesNet"
    __type__ = "hoster"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?hugefiles\.net/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Hugefiles.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "hugefiles.net"

    SIZE_PATTERN = r'<font style="color:#2574b6;"> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)'
