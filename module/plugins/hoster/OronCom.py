# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class OronCom(DeadHoster):
    __name__ = "OronCom"
    __type__ = "hoster"
    __version__ = "0.19"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?oron\.com/\w{12}'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Oron.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("chrox", "chrox@pyload.org"),
                   ("DHMH", "DHMH@pyload.org")]
