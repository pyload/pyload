# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class UptoboxCom(XFSPAccount):
    __name__ = "UptoboxCom"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """DDLStorage.com account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    MAIN_PAGE = "http://uptobox.com/"

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire: ([^<]+)</strong>'
