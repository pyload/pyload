# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class LomafileCom(XFSPAccount):
    __name__    = "LomafileCom"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """Lomafile.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_NAME = "lomafile.com"
