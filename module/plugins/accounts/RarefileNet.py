# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class RarefileNet(XFSPAccount):
    __name__ = "RarefileNet"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """RareFile.net account plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_URL = "http://www.rarefile.net/"
