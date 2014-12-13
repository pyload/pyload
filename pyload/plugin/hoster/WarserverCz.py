# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class WarserverCz(DeadHoster):
    __name    = "WarserverCz"
    __type    = "hoster"
    __version = "0.13"

    __pattern = r'http://(?:www\.)?warserver\.cz/stahnout/\d+'

    __description = """Warserver.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(WarserverCz)
