# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class File4safeCom(XFSPAccount):
    __name__ = "File4safeCom"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """File4safe.com account plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_URL = "http://www.file4safe.com/"

    LOGIN_FAIL_PATTERN = r'input_login'
    PREMIUM_PATTERN = r'Extend Premium'
