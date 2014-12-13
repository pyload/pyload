# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class UptoboxCom(XFSAccount):
    __name    = "UptoboxCom"
    __type    = "account"
    __version = "0.07"

    __description = """DDLStorage.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "uptobox.com"
    HOSTER_URL    = "https://uptobox.com/"
