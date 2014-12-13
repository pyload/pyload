# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class LinestorageCom(XFSAccount):
    __name    = "LinestorageCom"
    __type    = "account"
    __version = "0.02"

    __description = """Linestorage.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "linestorage.com"
