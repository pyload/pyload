# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class EpicShareNet(DeadHoster):
    __name__ = "EpicShareNet"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?epicshare\.net/\w{12}'

    __description__ = """EpicShare.net hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"


getInfo = create_getInfo(EpicShareNet)
