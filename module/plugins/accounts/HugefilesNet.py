# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class HugefilesNet(XFSPAccount):
    __name__ = "HugefilesNet"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Hugefiles.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.hugefiles.net/"
