# -*- coding: utf-8 -*-

from ..internal.XFSHoster import XFSHoster


class MovReelCom(XFSHoster):
    __name__ = "MovReelCom"
    __type__ = "hoster"
    __version__ = "1.31"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?movreel\.com/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """MovReel.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("JorisV83", "jorisv83-pyload@yahoo.com")]

    PLUGIN_DOMAIN = "movreel.com"

    LINK_PATTERN = r'<a href="(.+?)">Download Link'
