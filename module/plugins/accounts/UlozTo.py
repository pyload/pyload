# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.Account import Account


class UlozTo(Account):
    __name__    = "UlozTo"
    __type__    = "account"
    __version__ = "0.17"
    __status__  = "testing"

    __description__ = """Uloz.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("pulpe", None),
                       ("ondrej", "git@ondrej.it"),]


    TRAFFIC_LEFT_PATTERN = r'<a class="menu-kredit" href="/kredit" title="[^"]*?[MGT]+B = ([\d.]+) MB"'


    def grab_info(self, user, password, data):
        html = self.load("http://www.ulozto.net/")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)

        trafficleft = float(m.group(1).replace(' ', '').replace(',', '.')) * 1000 * 1.048 if m else 0
        premium     = True if trafficleft else False

        return {'validuntil': -1, 'trafficleft': trafficleft, 'premium': premium}


    def signin(self, user, password, data):
        login_page = self.load('http://www.ulozto.net/?do=web-login')
        action     = re.findall('<form action="(.+?)"', login_page)[1].replace('&amp;', '&')
        token      = re.search('_token_" value="(.+?)"', login_page).group(1)

        html = self.load(urlparse.urljoin("http://www.ulozto.net/", action),
                         post={'_token_' : token,
                               'do'      : "loginForm-submit",
                               'login'   : u"Přihlásit",
                               'password': password,
                               'username': user,
                               'remember': "on"})

        if '<div class="flash error">' in html:
            self.fail_login()
