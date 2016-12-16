# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.plugin.account import Account


class Http(Account):
    __name__ = "Http"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Http dummy account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    __config__ = [("domain", "str", "Domain", "")]

    login_timeout = info_threshold = 1000000

    def login(self, req):
        pass
