# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class KickloadCom(DeadHoster):
    __name    = "KickloadCom"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?kickload\.com/get/.+'

    __description = """Kickload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(KickloadCom)
