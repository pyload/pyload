# -*- coding: utf-8 -*-

from module.plugins.hoster.UnibytesCom import UnibytesCom
from module.plugins.internal.SimpleHoster import create_getInfo


class Share4webCom(UnibytesCom):
    __name__ = "Share4webCom"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?share4web\.com/get/\w+'

    __description__ = """Share4web.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    HOSTER_NAME = "share4web.com"


getInfo = create_getInfo(UnibytesCom)
