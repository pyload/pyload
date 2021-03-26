# -*- coding: utf-8 -*-

from ..base.account import BaseAccount


class Http(BaseAccount):
    __name__ = "Http"
    __type__ = "account"
    __version__ = "0.08"
    __status__ = "testing"

    __description__ = """Http dummy account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def grab_info(self, user, password, data):
        pass

    def signin(self, user, password, data):
        pass
