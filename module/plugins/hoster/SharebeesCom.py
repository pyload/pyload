# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SharebeesCom(DeadHoster):
    __name__ = "SharebeesCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?sharebees.com/\w{12}"
    __version__ = "0.02"
    __description__ = """ShareBees hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")


getInfo = create_getInfo(SharebeesCom)
