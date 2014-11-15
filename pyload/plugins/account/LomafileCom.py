# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class LomafileCom(XFSAccount):
    __name__    = "LomafileCom"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """Lomafile.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "lomafile.com"
