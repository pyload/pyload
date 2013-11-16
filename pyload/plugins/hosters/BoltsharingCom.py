# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class BoltsharingCom(XFileSharingPro):
    __name__ = "BoltsharingCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?boltsharing.com/\w{12}"
    __version__ = "0.01"
    __description__ = """Boltsharing.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    HOSTER_NAME = "boltsharing.com"


getInfo = create_getInfo(BoltsharingCom)
