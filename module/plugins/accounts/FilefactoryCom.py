# -*- coding: utf-8 -*-

import pycurl
import re
import time

from module.plugins.internal.Account import Account


class FilefactoryCom(Account):
    __name__    = "FilefactoryCom"
    __type__    = "account"
    __version__ = "0.17"
    __status__  = "testing"

    __description__ = """Filefactory.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    VALID_UNTIL_PATTERN = r'Premium valid until: <strong>(?P<D>\d{1,2})\w{1,2} (?P<M>\w{3}), (?P<Y>\d{4})</strong>'


    def parse_info(self, user, password, data, req):
        html = self.load("http://www.filefactory.com/account/")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            premium = True
            validuntil = re.sub(self.VALID_UNTIL_PATTERN, '\g<D> \g<M> \g<Y>', m.group(0))
            validuntil = time.mktime(time.strptime(validuntil, "%d %b %Y"))
        else:
            premium = False
            validuntil = -1

        return {'premium': premium, 'trafficleft': -1, 'validuntil': validuntil}


    def login(self, user, password, data, req):
        req.http.c.setopt(pycurl.REFERER, "http://www.filefactory.com/member/login.php")

        html = self.load("https://www.filefactory.com/member/signin.php",
                         post={'loginEmail'   : user,
                               'loginPassword': password,
                               'Submit'       : "Sign In"})

        if req.lastEffectiveURL != "http://www.filefactory.com/account/":
            self.login_fail()
