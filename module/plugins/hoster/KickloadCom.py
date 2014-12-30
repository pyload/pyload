# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class KickloadCom(DeadHoster):
    __name__    = "KickloadCom"
    __type__    = "hoster"
    __version__ = "0.21"

    __pattern__ = r'http://(?:www\.)?kickload\.com/get/.+'

    __description__ = """Kickload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(KickloadCom)
