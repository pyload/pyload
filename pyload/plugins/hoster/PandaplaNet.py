# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class PandaplaNet(DeadHoster):
    __name    = "PandaplaNet"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?pandapla\.net/\w{12}'

    __description = """Pandapla.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


getInfo = create_getInfo(PandaplaNet)
