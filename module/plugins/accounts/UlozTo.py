# -*- coding: utf-8 -*-

import re

from module.plugins.Account import Account


class UlozTo(Account):
    __name__ = "UlozTo"
    __type__ = "account"
    __version__ = "0.06"

    __description__ = """Uloz.to account plugin"""
    __author_name__ = ("zoidberg", "pulpe")
    __author_mail__ = "zoidberg@mujmail.cz"

    TRAFFIC_LEFT_PATTERN = r'<li class="menu-kredit"><a href="/kredit" title="[^"]*?GB = ([0-9.]+) MB"'


    def loadAccountInfo(self, user, req):
        #this cookie gets lost somehow after each request
        self.phpsessid = req.cj.getCookie("ULOSESSID")
        html = req.load("http://www.ulozto.net/", decode=True)
        req.cj.setCookie("www.ulozto.net", "ULOSESSID", self.phpsessid)

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        trafficleft = int(float(m.group(1).replace(' ', '').replace(',', '.')) * 1000 * 1.048) if m else 0
        self.premium = True if trafficleft else False

        return {"validuntil": -1, "trafficleft": trafficleft}

    def login(self, user, data, req):
        login_page = req.load('http://www.ulozto.net/?do=web-login', decode=True)
        action = re.findall('<form action="(.+?)"', login_page)[1].replace('&amp;', '&')
        token = re.search('_token_" value="(.+?)"', login_page).group(1)

        html = req.load('http://www.ulozto.net'+action, post={
            "_token_": token,
            "login": "Submit",
            "password": data['password'],
            "username": user
        }, decode=True)

        if '<div class="flash error">' in html:
            self.wrongPassword()
