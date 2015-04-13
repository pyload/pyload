# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class KickloadCom(DeadHoster):
    __name__    = "KickloadCom"
    __type__    = "hoster"
    __version__ = "0.21"

    __pattern__ = r'http://(?:www\.)?kickload\.com/get/.+'
    __config__  = []

    __description__ = """Kickload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]
