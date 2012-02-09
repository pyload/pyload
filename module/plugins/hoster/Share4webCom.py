# -*- coding: utf-8 -*-

from module.plugins.hoster.UnibytesCom import UnibytesCom
from module.plugins.internal.SimpleHoster import create_getInfo

class Share4webCom(UnibytesCom):
    __name__ = "Share4webCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?share4web\.com/get/\w+"
    __version__ = "0.1"
    __description__ = """Share4web.com"""
    __author_name__ = ("zoidberg")
    
    DOMAIN = 'http://www.share4web.com'

getInfo = create_getInfo(UnibytesCom)