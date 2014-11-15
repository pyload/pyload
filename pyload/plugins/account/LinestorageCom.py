# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class LinestorageCom(XFSAccount):
    __name__    = "LinestorageCom"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """Linestorage.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "linestorage.com"
