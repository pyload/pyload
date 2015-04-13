# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class LinestorageCom(XFSAccount):
    __name    = "LinestorageCom"
    __type    = "account"
    __version = "0.03"

    __description = """Linestorage.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "linestorage.com"
    HOSTER_URL    = "http://linestorage.com/"
