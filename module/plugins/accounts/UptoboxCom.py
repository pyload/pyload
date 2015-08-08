# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class UptoboxCom(XFSAccount):
    __name__    = "UptoboxCom"
    __type__    = "account"
    __version__ = "0.09"
    __status__  = "testing"

    __description__ = """DDLStorage.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "uptobox.com"
    HOSTER_URL    = "https://uptobox.com/"
    LOGIN_URL     = "https://login.uptobox.com/"
