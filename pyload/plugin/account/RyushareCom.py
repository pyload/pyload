# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class RyushareCom(XFSAccount):
    __name    = "RyushareCom"
    __type    = "account"
    __version = "0.06"

    __description = """Ryushare.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "ryushare.com"
