# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class File4SafeCom(XFSAccount):
    __name__    = "File4SafeCom"
    __type__    = "account"
    __version__ = "0.06"
    __status__  = "testing"

    __description__ = """File4Safe.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "file4safe.com"

    LOGIN_FAIL_PATTERN = r'input_login'
