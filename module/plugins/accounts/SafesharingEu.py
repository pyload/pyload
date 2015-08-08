# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class SafesharingEu(XFSAccount):
    __name__    = "SafesharingEu"
    __type__    = "account"
    __version__ = "0.03"
    __status__  = "testing"

    __description__ = """Safesharing.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "safesharing.eu"
