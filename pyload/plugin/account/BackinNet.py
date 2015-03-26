# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class BackinNet(XFSAccount):
    __name    = "BackinNet"
    __type    = "account"
    __version = "0.01"

    __description = """Backin.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "backin.net"
