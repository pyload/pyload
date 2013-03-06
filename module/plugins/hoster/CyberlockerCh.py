# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class CyberlockerCh(XFileSharingPro):
    __name__ = "CyberlockerCh"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?cyberlocker\.ch/\w{12}"
    __version__ = "0.01"
    __description__ = """Cyberlocker.ch hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    HOSTER_NAME = "cyberlocker.ch"

getInfo = create_getInfo(CyberlockerCh)
