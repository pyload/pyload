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
    __version__ = "0.10"

    __description__ = """XFileSharingPro base account plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = None

    COOKIES = None  #: or list of tuples [(domain, name, value)]

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire:.*?<b>(.+?)</b>'
    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:.*?<b>(?P<S>.+?)</b>'
    LOGIN_FAIL_PATTERN = r'>(Incorrect Login or Password|Error<)'
    # PREMIUM_PATTERN = r'>Renew premium<'


    def loadAccountInfo(self, user, req):
        html = req.load(self.HOSTER_URL, get={'op': "my_account"}, decode=True)

        validuntil = None
        trafficleft = None
        premium = None

        if hasattr(self, "PREMIUM_PATTERN"):
            premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1)
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%d %B %Y"))
            except Exception, e:
                self.logError(e)
            else:
                if validuntil > mktime(gmtime()):
                    premium = True
                    trafficleft = -1
                else:
                    if premium is False:  #: registered account type (not premium)
                        validuntil = -1
                    premium = False

        try:
            traffic = re.search(self.TRAFFIC_LEFT_PATTERN, html).groupdict()
            trafficsize = traffic['S'] + traffic['U'] if 'U' in traffic else traffic['S']
            if "Unlimited" in trafficsize:
                trafficleft = -1
                if premium is None:
                    premium = True
            else:
                trafficleft = parseFileSize(trafficsize)
        except:
            pass

        if premium is None:
            premium = False

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, data, req):
        if isinstance(self.COOKIES, list):
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
