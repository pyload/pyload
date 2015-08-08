# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class CramitIn(XFSAccount):
    __name__    = "CramitIn"
    __type__    = "account"
    __version__ = "0.04"
    __status__  = "testing"

    __description__ = """Cramit.in account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "cramit.in"
