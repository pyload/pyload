# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount


class SpeedLoadOrg(XFSPAccount):
    __name__ = "SpeedLoadOrg"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """SpeedLoadOrg account plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    MAIN_PAGE = "http://speedload.org/"
