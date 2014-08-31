# -*- coding: utf-8 -*-

import re
from time import strptime, mktime
from pycurl import REFERER

from module.plugins.Account import Account


class OneFichierCom(Account):
    __name__ = "OneFichierCom"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """1fichier.com account plugin"""
    __author_name__ = "Elrick69"
    __author_mail__ = "elrick69[AT]rocketmail[DOT]com"

    VALID_UNTIL_PATTERN = r'You are a premium user until (?P<d>\d{2})/(?P<m>\d{2})/(?P<y>\d{4})'


    def loadAccountInfo(self, user, req):

        html = req.load("http://1fichier.com/console/abo.pl")

        m = re.search(self.VALID_UNTIL_PATTERN, html)

        if m:
            premium = True
            validuntil = re.sub(self.VALID_UNTIL_PATTERN, '\g<d>/\g<m>/\g<y>', m.group(0))
            validuntil = int(mktime(strptime(validuntil, "%d/%m/%Y")))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def login(self, user, data, req):

        req.http.c.setopt(REFERER, "http://1fichier.com/login.pl?lg=en")

        html = req.load("http://1fichier.com/login.pl?lg=en", post={
            "mail": user,
            "pass": data['password'],
            "Login": "Login"})

        if r'<div class="error_message">Invalid username or password.</div>' in html:
            self.wrongPassword()
