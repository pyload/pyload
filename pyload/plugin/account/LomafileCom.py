# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class LomafileCom(XFSAccount):
    __name    = "LomafileCom"
    __type    = "account"
    __version = "0.02"

    __description = """Lomafile.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "lomafile.com"
