# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SharebeesCom(DeadHoster):
    __name__    = "SharebeesCom"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?sharebees\.com/\w{12}'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """ShareBees hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(SharebeesCom)
