# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class WarserverCz(DeadHoster):
    __name__    = "WarserverCz"
    __type__    = "hoster"
    __version__ = "0.13"

    __pattern__ = r'http://(?:www\.)?warserver\.cz/stahnout/\d+'

    __description__ = """Warserver.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(WarserverCz)
