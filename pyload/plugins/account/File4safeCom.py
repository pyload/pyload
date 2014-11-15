# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class File4safeCom(XFSAccount):
    __name__    = "File4safeCom"
    __type__    = "account"
    __version__ = "0.04"

    __description__ = """File4safe.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "file4safe.com"

    LOGIN_FAIL_PATTERN = r'input_login'
