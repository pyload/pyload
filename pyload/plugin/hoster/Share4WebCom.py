# -*- coding: utf-8 -*-

from pyload.plugin.hoster.UnibytesCom import UnibytesCom


class Share4WebCom(UnibytesCom):
    __name__    = "Share4WebCom"
    __type__    = "hoster"
    __version__ = "0.11"

    __pattern__ = r'https?://(?:www\.)?share4web\.com/get/\w+'

    __description__ = """Share4web.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "share4web.com"
