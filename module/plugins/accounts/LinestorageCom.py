# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class LinestorageCom(XFSAccount):
    __name__    = "LinestorageCom"
    __type__    = "account"
    __version__ = "0.04"
    __status__  = "testing"

    __description__ = """Linestorage.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "linestorage.com"
    HOSTER_URL    = "http://linestorage.com/"
