# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class UptoboxCom(XFSAccount):
    __name__    = "UptoboxCom"
    __type__    = "account"
    __version__ = "0.06"

    __description__ = """DDLStorage.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "uptobox.com"
