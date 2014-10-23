# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class SafesharingEu(XFSPAccount):
    __name__ = "SafesharingEu"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Safesharing.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_URL = "http://www.safesharing.eu/"
