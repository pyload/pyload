# -*- coding: utf-8 -*-

from ..internal.XFSHoster import XFSHoster


class JunocloudMe(XFSHoster):
    __name__ = "JunocloudMe"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r'http://(?:\w+\.)?junocloud\.me/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Junocloud.me hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]

    PLUGIN_DOMAIN = "junocloud.me"

    URL_REPLACEMENTS = [(r'//(www\.)?junocloud', "//dl3.junocloud")]

    OFFLINE_PATTERN = r'>No such file with this filename<'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'
