# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class File4SafeCom(XFSAccount):
    __name    = "File4SafeCom"
    __type    = "account"
    __version = "0.05"

    __description = """File4Safe.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "file4safe.com"

    LOGIN_FAIL_PATTERN = r'input_login'
