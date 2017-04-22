# -*- coding: utf-8 -*-

from .UnibytesCom import UnibytesCom


class Share4WebCom(UnibytesCom):
    __name__ = "Share4WebCom"
    __type__ = "hoster"
    __version__ = "0.17"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?share4web\.com/get/\w+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Share4web.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    PLUGIN_DOMAIN = "share4web.com"
