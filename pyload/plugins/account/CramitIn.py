# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class CramitIn(XFSAccount):
    __name    = "CramitIn"
    __type    = "account"
    __version = "0.03"

    __description = """Cramit.in account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "cramit.in"
