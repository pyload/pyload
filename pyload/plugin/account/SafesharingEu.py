# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class SafesharingEu(XFSAccount):
    __name    = "SafesharingEu"
    __type    = "account"
    __version = "0.02"

    __description = """Safesharing.eu account plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "safesharing.eu"
