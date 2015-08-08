# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class HugefilesNet(XFSAccount):
    __name__    = "HugefilesNet"
    __type__    = "account"
    __version__ = "0.03"
    __status__  = "testing"

    __description__ = """Hugefiles.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "hugefiles.net"
