# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class OronCom(DeadHoster):
    __name__    = "OronCom"
    __type__    = "hoster"
    __version__ = "0.14"

    __pattern__ = r'https?://(?:www\.)?oron\.com/\w{12}'

    __description__ = """Oron.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("chrox", "chrox@pyload.org"),
                       ("DHMH", "DHMH@pyload.org")]


getInfo = create_getInfo(OronCom)
