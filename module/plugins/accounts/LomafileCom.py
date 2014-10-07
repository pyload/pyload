# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class LomafileCom(XFSPAccount):
    __name__ = "LomafileCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Lomafile.com account plugin"""
    __author_name__ = "guidobelix"
    __author_mail__ = "guidobelix@hotmail.it"


    HOSTER_URL = "http://www.lomafile.com/"
