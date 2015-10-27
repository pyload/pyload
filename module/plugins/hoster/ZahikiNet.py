# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ZahikiNet(DeadHoster):
    __name__    = "ZahikiNet"
    __type__    = "hoster"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?zahiki\.net/\w+/.+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Zahiki.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(ZahikiNet)
