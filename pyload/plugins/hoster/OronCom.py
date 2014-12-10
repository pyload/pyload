# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class OronCom(DeadHoster):
    __name    = "OronCom"
    __type    = "hoster"
    __version = "0.14"

    __pattern = r'https?://(?:www\.)?oron\.com/\w{12}'

    __description = """Oron.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("chrox", "chrox@pyload.org"),
                       ("DHMH", "DHMH@pyload.org")]


getInfo = create_getInfo(OronCom)
