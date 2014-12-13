# -*- coding: utf-8 -*-

from pyload.plugin.hoster.UnibytesCom import UnibytesCom
from pyload.plugin.internal.SimpleHoster import create_getInfo


class Share4webCom(UnibytesCom):
    __name    = "Share4webCom"
    __type    = "hoster"
    __version = "0.11"

    __pattern = r'https?://(?:www\.)?share4web\.com/get/\w+'

    __description = """Share4web.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "share4web.com"


getInfo = create_getInfo(UnibytesCom)
