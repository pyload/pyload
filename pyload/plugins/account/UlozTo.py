# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from pyload.plugins.Account import Account


class UlozTo(Account):
    __name__    = "UlozTo"
    __type__    = "account"
    __version__ = "0.07"

    __description__ = """Uloz.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("pulpe", None)]


    TRAFFIC_LEFT_PATTERN = r'<li class="menu-kredit"><a href="/kredit" title="[^"]*?GB = ([\d.]+) MB"'


    def loadAccountInfo(self, user, req):
        self.phpsessid = req.cj.getCookie("ULOSESSID")  #@NOTE: this cookie gets lost somehow after each request

        html = req.load("http://www.ulozto.net/", decode=True)

        req.cj.setCookie("ulozto.net", "ULOSESSID", self.phpsessid)

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        trafficleft = int(float(m.group(1).replace(' ', '').replace(',', '.')) * 1000 * 1.048) if m else 0
        self.premium = True if trafficleft else False

        return {"validuntil": -1, "trafficleft": trafficleft}


    def login(self, user, data, req):
        login_page = req.load('http://www.ulozto.net/?do=web-login', decode=True)
        action = re.findall('<form action="(.+?)"', login_page)[1].replace('&amp;', '&')
        token = re.search('_token_" value="(.+?)"', login_page).group(1)

        html = req.load(urljoin("http://www.ulozto.net/", action),
                        post={'_token_' : token,
                              'do'      : "loginForm-submit",
                              'login'   : u"Přihlásit",
                              'password': data['password'],
                              'username': user},
                        decode=True)

        if '<div class="flash error">' in html:
            self.wrongPassword()
