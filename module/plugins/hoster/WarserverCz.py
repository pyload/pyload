# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class WarserverCz(DeadHoster):
    __name__    = "WarserverCz"
    __type__    = "hoster"
    __version__ = "0.14"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?warserver\.cz/stahnout/\d+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Warserver.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(WarserverCz)
