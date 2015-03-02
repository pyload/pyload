# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.Account import Account


def realSize(size):
  if size == "M":
    return 1.024  
  elif size == "G":
    return 1.048
  elif size == "T":
    return 1.072
  else:
    return 1.0

class UlozTo(Account):
    __name__    = "UlozTo"
    __type__    = "account"
    __version__ = "0.11"

    __description__ = """Uloz.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("pulpe", None)]


    TRAFFIC_LEFT_PATTERN = r'<li class="menu-kredit"><a .*?title="[^"]*?([MGT]+)B = ([\d.]+) MB"'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.ulozto.net/", decode=True)

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)

        trafficleft = float(m.group(2).replace(' ', '').replace(',', '.')) * 1000 * realSize(m.group(1)) if m else 0
        premium     = True if trafficleft else False

        return {'validuntil': -1, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, data, req):
        login_page = req.load('http://www.ulozto.net/?do=web-login', decode=True)
        action     = re.findall('<form action="(.+?)"', login_page)[1].replace('&amp;', '&')
        token      = re.search('_token_" value="(.+?)"', login_page).group(1)

        html = req.load(urljoin("http://www.ulozto.net/", action),
                        post={'_token_' : token,
                              'do'      : "loginForm-submit",
                              'login'   : u"Přihlásit",
                              'password': data['password'],
                              'username': user,
                              'remember': "on"},
                        decode=True)

        if '<div class="flash error">' in html:
            self.wrongPassword()
