# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class UptoboxCom(XFSPAccount):
    __name__    = "UptoboxCom"
    __type__    = "account"
    __version__ = "0.05"

    __description__ = """DDLStorage.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_NAME = "uptobox.com"

    PREMIUM_PATTERN = r'class="premium_time"'
