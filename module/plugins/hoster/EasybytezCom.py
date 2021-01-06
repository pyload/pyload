# -*- coding: utf-8 -*-

from ..internal.XFSHoster import XFSHoster


class EasybytezCom(XFSHoster):
    __name__ = "EasybytezCom"
    __type__ = "hoster"
    __version__ = "0.30"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?easybytez\.com/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Easybytez.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it")]

    PLUGIN_DOMAIN = "easybytez.com"

    OFFLINE_PATTERN = r'>File not available'

    LINK_PATTERN = r'(http://(\w+\.(easybytez|easyload|ezbytez|ezybytez|zingload)\.(com|to)|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/.+?)["\'<]'
