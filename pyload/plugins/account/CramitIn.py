# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class CramitIn(XFSPAccount):
    __name__ = "CramitIn"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Cramit.in account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    MAIN_PAGE = "http://cramit.in/"
