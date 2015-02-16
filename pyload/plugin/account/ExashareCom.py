# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class ExashareCom(XFSAccount):
    __name    = "ExashareCom"
    __type    = "account"
    __version = "0.01"

    __description = """Exashare.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "exashare.com"
