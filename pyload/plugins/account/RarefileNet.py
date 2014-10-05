# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class RarefileNet(XFSPAccount):
    __name__ = "RarefileNet"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """RareFile.net account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    HOSTER_URL = "http://rarefile.net/"
