# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class ZahikiNet(DeadHoster):
    __name__ = "ZahikiNet"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?zahiki\.net/\w+/.+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Zahiki.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
