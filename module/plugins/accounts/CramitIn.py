# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class CramitIn(XFSPAccount):
    __name__ = "CramitIn"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """Cramit.in account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    HOSTER_URL = "http://www.cramit.in/"
