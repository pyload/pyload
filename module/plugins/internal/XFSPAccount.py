# -*- coding: utf-8 -*-

import re

from time import mktime, strptime

from module.plugins.Account import Account
from module.plugins.internal.SimpleHoster import parseHtmlForm
from module.utils import parseFileSize


class XFSPAccount(Account):
    __name__ = "XFSPAccount"
    __type__ = "account"
    __version__ = "0.06"

    __description__ = """XFileSharingPro base account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    MAIN_PAGE = None

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire:</TD><TD><b>([^<]+)</b>'
    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:</TD><TD><b>([^<]+)</b>'
    LOGIN_FAIL_PATTERN = r'Incorrect Login or Password|>Error<'
    PREMIUM_PATTERN = r'>Renew premium<'


    def loadAccountInfo(self, user, req):
        html = req.load(self.MAIN_PAGE + "?op=my_account", decode=True)

        validuntil = trafficleft = None
        premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            premium = True
            trafficleft = -1
            try:
                self.logDebug(m.group(1))
                validuntil = mktime(strptime(m.group(1), "%d %B %Y"))
            except Exception, e:
                self.logError(e)
        else:
            m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
            if m:
                trafficleft = m.group(1)
                if "Unlimited" in trafficleft:
                    premium = True
                else:
                    trafficleft = parseFileSize(trafficleft) / 1024

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}

    def login(self, user, data, req):
        html = req.load('%slogin.html' % self.MAIN_PAGE, decode=True)

        action, inputs = parseHtmlForm('name="FL"', html)
        if not inputs:
            inputs = {"op": "login",
                      "redirect": self.MAIN_PAGE}

        inputs.update({"login": user,
                       "password": data['password']})

        html = req.load(self.MAIN_PAGE, post=inputs, decode=True)

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.wrongPassword()
