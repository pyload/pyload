# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class UptoboxCom(XFSPAccount):
    __name__ = "UptoboxCom"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """DDLStorage.com account plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_URL = "http://www.uptobox.com/"

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire: ([^<]+)</strong>'
