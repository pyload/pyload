# -*- coding: utf-8 -*-

import re

from ..internal.Account import Account


class YibaishiwuCom(Account):
    __name__ = "YibaishiwuCom"
    __type__ = "account"
    __version__ = "0.09"
    __status__ = "testing"

    __description__ = """115.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    ACCOUNT_INFO_PATTERN = r'var USER_PERMISSION = {(.*?)}'

    def grab_info(self, user, password, data):
        html = self.load("http://115.com/")

        m = re.search(self.ACCOUNT_INFO_PATTERN, html, re.S)
        premium = True if m and 'is_vip: 1' in m.group(1) else False
        validuntil = trafficleft = (-1 if m else 0)
        return dict({'validuntil': validuntil,
                     'trafficleft': trafficleft, 'premium': premium})

    def signin(self, user, password, data):
        html = self.load("https://passport.115.com/?ac=login",
                         post={'back': "http://www.115.com/",
                               'goto': "http://115.com/",
                               "login[account]": user,
                               "login[passwd]": password})

        if not 'var USER_PERMISSION = {' in html:
            self.fail_login()
