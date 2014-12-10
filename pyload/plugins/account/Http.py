# -*- coding: utf-8 -*-

from pyload.plugins.Account import Account


class Http(Account):
    __name    = "Http"
    __type    = "account"
    __version = "0.01"

    __description = """Http dummy account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    login_timeout  = -1  #: Unlimited
    info_threshold = -1  #: Unlimited
