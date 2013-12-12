# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class BoltsharingCom(DeadHoster):
    __name__ = "BoltsharingCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?boltsharing.com/\w{12}"
    __version__ = "0.02"
    __description__ = """Boltsharing.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")


getInfo = create_getInfo(BoltsharingCom)
