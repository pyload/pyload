# -*- coding: utf-8 -*-

import re
from time import mktime, strptime

from pycurl import REFERER

from module.plugins.Account import Account


class FilefactoryCom(Account):
    __name__    = "FilefactoryCom"
    __type__    = "account"
    __version__ = "0.15"

    __description__ = """Filefactory.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    VALID_UNTIL_PATTERN = r'Premium valid until: <strong>(?P<D>\d{1,2})\w{1,2} (?P<M>\w{3}), (?P<Y>\d{4})</strong>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.filefactory.com/account/")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            premium = True
            validuntil = re.sub(self.VALID_UNTIL_PATTERN, '\g<D> \g<M> \g<Y>', m.group(0))
            validuntil = mktime(strptime(validuntil, "%d %b %Y"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}


    def login(self, user, data, req):
        req.http.c.setopt(REFERER, "http://www.filefactory.com/member/login.php")

        html = req.load("http://www.filefactory.com/member/signin.php",
                        post={"loginEmail"   : user,
                              "loginPassword": data['password'],
                              "Submit"       : "Sign In"})

        if req.lastEffectiveURL != "http://www.filefactory.com/account/":
            self.wrongPassword()
