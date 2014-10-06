# -*- coding: utf-8 -*-

import re

from urlparse import urljoin
from time import mktime, strptime

from module.plugins.Account import Account
from module.plugins.internal.SimpleHoster import parseHtmlForm, set_cookies
from module.utils import parseFileSize


class XFSPAccount(Account):
    __name__ = "XFSPAccount"
    __type__ = "account"
    __version__ = "0.08"

    __description__ = """XFileSharingPro base account plugin"""
    __author_name__ = ("zoidberg", "Walter Purcaro")
    __author_mail__ = ("zoidberg@mujmail.cz", "vuolter@gmail.com")


    HOSTER_URL = None

    COOKIES = None  #: or list of tuples [(domain, name, value)]

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire:.*?<b>(.+?)</b>'
    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:.*?<b>(.+?)</b>'
    LOGIN_FAIL_PATTERN = r'>(Incorrect Login or Password|Error<)'
    PREMIUM_PATTERN = r'>Renew premium<'


    def loadAccountInfo(self, user, req):
        html = req.load(self.HOSTER_URL, get={'op': "my_account"}, decode=True)

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

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, data, req):
        set_cookies(req.cj, self.COOKIES)

        url = urljoin(self.HOSTER_URL, "login.html")
        html = req.load(url, decode=True)

        action, inputs = parseHtmlForm('name="FL"', html)
        if not inputs:
            inputs = {'op': "login",
                      'redirect': self.HOSTER_URL}

        inputs.update({'login': user,
                       'password': data['password']})

        html = req.load(self.HOSTER_URL, post=inputs, decode=True)

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.wrongPassword()
