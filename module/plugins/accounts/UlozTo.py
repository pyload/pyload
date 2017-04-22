# -*- coding: utf-8 -*-

import re
import urlparse

from ..internal.Account import Account


class UlozTo(Account):
    __name__ = "UlozTo"
    __type__ = "account"
    __version__ = "0.23"
    __status__ = "testing"

    __description__ = """Uloz.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("pulpe", None),
                   ("ondrej", "git@ondrej.it"), ]

    TRAFFIC_LEFT_PATTERN = r'<span class="user"><i class="fi fi-user"></i> <em>.+</em> \(([^ ]+) ([MGT]+B)\)</span>'

    def grab_info(self, user, password, data):
        html = self.load("https://www.ulozto.net/")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)

        trafficleft = self.parse_traffic(m.group(1), m.group(2))
        premium = True if trafficleft else False

        return {'validuntil': -1, 'trafficleft': trafficleft, 'premium': premium}

    def signin(self, user, password, data):
        login_page = self.load('https://www.ulozto.net/?do=web-login')
        action = re.findall(
            '<form action="(.+?)"',
            login_page)[1].replace(
            '&amp;',
            '&')
        token = re.search('_token_" value="(.+?)"', login_page).group(1)

        html = self.load(urlparse.urljoin("https://www.ulozto.net/", action),
                         post={'_token_': token,
                               '_do': "loginForm-submit",
                               'login': u"Submit",
                               'password': password,
                               'username': user})

        if '<div class="flash error">' in html:
            self.fail_login()
