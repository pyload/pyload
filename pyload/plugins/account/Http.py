# -*- coding: utf-8 -*-

from pyload.plugins.internal.Account import Account


class Http(Account):
    __name__    = "Http"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """Http dummy account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    login_timeout  = -1  #: Unlimited
    info_threshold = -1  #: Unlimited
