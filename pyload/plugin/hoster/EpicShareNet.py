# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class EpicShareNet(DeadHoster):
    __name__    = "EpicShareNet"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?epicshare\.net/\w{12}'

    __description__ = """EpicShare.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
