# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class KickloadCom(DeadHoster):
    __name__ = "KickloadCom"
    __type__ = "hoster"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?kickload\.com/get/.+'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Kickload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de")]
