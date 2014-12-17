# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class LinestorageCom(XFSHoster):
    __name__    = "LinestorageCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?linestorage\.com/\w{12}'

    __description__ = """Linestorage.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "linestorage.com"


getInfo = create_getInfo(LinestorageCom)
