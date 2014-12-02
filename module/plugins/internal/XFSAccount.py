# -*- coding: utf-8 -*-

import re

from time import gmtime, mktime, strptime
from urlparse import urljoin

from module.plugins.Account import Account
from module.plugins.internal.SimpleHoster import parseHtmlForm, set_cookies


class XFSAccount(Account):
    __name__    = "XFSAccount"
    __type__    = "account"
    __version__ = "0.32"

    __description__ = """XFileSharing account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None
    HOSTER_URL    = None

    COOKIES = [(HOSTER_DOMAIN, "lang", "english")]

    PREMIUM_PATTERN = r'\(Premium only\)'

    VALID_UNTIL_PATTERN = r'Premium.[Aa]ccount expire:.*?(\d{1,2} [\w^_]+ \d{4})'

    TRAFFIC_LEFT_PATTERN = r'Traffic available today:.*?<b>\s*(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</b>'
    TRAFFIC_LEFT_UNIT    = "MB"  #: used only if no group <U> was found

    LEECH_TRAFFIC_PATTERN = r'Leech Traffic left:<b>.*?(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</b>'
    LEECH_TRAFFIC_UNIT    = "MB"  #: used only if no group <U> was found

    LOGIN_FAIL_PATTERN = r'>\s*(Incorrect Login or Password|Error<)'


    def __init__(self, manager, accounts):  #@TODO: remove in 0.4.10
        self.init()
        return super(XFSAccount, self).__init__(manager, accounts)


    def init(self):
        # if not self.HOSTER_DOMAIN:
            # self.fail(_("Missing HOSTER_DOMAIN"))

        if not self.HOSTER_URL:
            self.HOSTER_URL = "http://www.%s/" % self.HOSTER_DOMAIN


    def loadAccountInfo(self, user, req):
        validuntil   = None
        trafficleft  = None
        leechtraffic = None
        premium      = None

        html = req.load(self.HOSTER_URL, get={'op': "my_account"}, decode=True)

        premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%d %B %Y"))

            except Exception, e:
                self.logError(e)

            else:
                self.logDebug("Valid until: %s" % validuntil)

                if validuntil > mktime(gmtime()):
                    premium = True
                    trafficleft = -1
                else:
                    premium = False
                    validuntil = None  #: registered account type (not premium)
        else:
            self.logDebug("VALID_UNTIL_PATTERN not found")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            try:
                traffic = m.groupdict()
                size    = traffic['S']

                if "nlimited" in size:
                    trafficleft = -1
                    if validuntil is None:
                        validuntil = -1
                else:
                    if 'U' in traffic:
                        unit = traffic['U']
                    elif isinstance(self.TRAFFIC_LEFT_UNIT, basestring):
                        unit = self.TRAFFIC_LEFT_UNIT
                    else:
                        unit = ""

                    trafficleft = self.parseTraffic(size + unit)

            except Exception, e:
                self.logError(e)
        else:
            self.logDebug("TRAFFIC_LEFT_PATTERN not found")

        leech = [m.groupdict() for m in re.finditer(self.LEECH_TRAFFIC_PATTERN, html)]
        if leech:
            leechtraffic = 0
            try:
                for traffic in leech:
                    size = traffic['S']

                    if "nlimited" in size:
                        leechtraffic = -1
                        if validuntil is None:
                            validuntil = -1
                        break
                    else:
                        if 'U' in traffic:
                            unit = traffic['U']
                        elif isinstance(self.LEECH_TRAFFIC_UNIT, basestring):
                            unit = self.LEECH_TRAFFIC_UNIT
                        else:
                            unit = ""

                        leechtraffic += self.parseTraffic(size + unit)

            except Exception, e:
                self.logError(e)
        else:
            self.logDebug("LEECH_TRAFFIC_PATTERN not found")

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'leechtraffic': leechtraffic, 'premium': premium}


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
