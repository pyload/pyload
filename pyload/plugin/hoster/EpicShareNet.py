# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class EpicShareNet(DeadHoster):
    __name    = "EpicShareNet"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'https?://(?:www\.)?epicshare\.net/\w{12}'

    __description = """EpicShare.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
