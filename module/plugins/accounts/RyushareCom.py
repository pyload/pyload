# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class RyushareCom(XFSAccount):
    __name__    = "RyushareCom"
    __type__    = "account"
    __version__ = "0.09"
    __status__  = "testing"

    __description__ = """Ryushare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = "ryushare.com"
