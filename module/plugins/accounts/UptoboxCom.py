# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class UptoboxCom(XFSPAccount):
    __name__ = "UptoboxCom"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """DDLStorage.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_NAME = "uptobox.com"

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire: ([^<]+)</strong>'
