# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class XvidstageCom(XFileSharingPro):
    __name__ = "XvidstageCom"
    __type__ = "hoster"
    __pattern__ = r"http://xvidstage.com/.*"
    __version__ = "1.00"
    __description__ = """Xvidstage.com hoster plugin"""
    __author_name__ = ("JorisV83")
    __author_mail__ = ("jorisv83-pyload@yahoo.com")

    HOSTER_NAME = "Xvidstage.com"    

getInfo = create_getInfo(XvidstageCom)