# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class HugefilesNet(XFSAccount):
    __name    = "HugefilesNet"
    __type    = "account"
    __version = "0.02"

    __description = """Hugefiles.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "hugefiles.net"
