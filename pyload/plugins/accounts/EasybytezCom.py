# -*- coding: utf-8 -*-

import re
from time import mktime, strptime, gmtime

from pyload.plugins.Account import Account
from pyload.plugins.internal.SimpleHoster import parseHtmlForm
from pyload.utils import parseFileSize


class EasybytezCom(Account):
    __name__ = "EasybytezCom"
    __type__ = "account"
    __version__ = "0.06"

    __description__ = """EasyBytez.com account plugin"""
    __author_name__ = ("zoidberg", "guidobelix")
    __author_mail__ = ("zoidberg@mujmail.cz", "guidobelix@hotmail.it")

    VALID_UNTIL_PATTERN = r'Premium account expire:</TD><TD><b>([^<]+)</b>'
    TRAFFIC_LEFT_PATTERN = r'<TR><TD>Traffic available today:</TD><TD><b>(?P<S>[^<]+)</b>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.easybytez.com/?op=my_account", decode=True)

        validuntil = None
        trafficleft = None
        premium = False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1)
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%d %B %Y"))
            except Exception, e:
                self.logError(e)

            if validuntil > mktime(gmtime()):
                premium = True
                trafficleft = -1
            else:
                premium = False
                validuntil = -1

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = m.group(1)
            if "Unlimited" in trafficleft:
                trafficleft = -1
            else:
                trafficleft = parseFileSize(trafficleft) / 1024

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}


    def login(self, user, data, req):
        html = req.load('http://www.easybytez.com/login.html', decode=True)
        action, inputs = parseHtmlForm('name="FL"', html)
        inputs.update({"login": user,
                       "password": data['password'],
                       "redirect": "http://www.easybytez.com/"})

        html = req.load(action, post=inputs, decode=True)

        if 'Incorrect Login or Password' in html or '>Error<' in html:
            self.wrongPassword()
