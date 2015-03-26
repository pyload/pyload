# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class PandaplaNet(DeadHoster):
    __name    = "PandaplaNet"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?pandapla\.net/\w{12}'
    __config  = []

    __description = """Pandapla.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
