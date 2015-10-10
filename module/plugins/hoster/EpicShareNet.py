# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class EpicShareNet(DeadHoster):
    __name__    = "EpicShareNet"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?epicshare\.net/\w{12}'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """EpicShare.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


getInfo = create_getInfo(EpicShareNet)
