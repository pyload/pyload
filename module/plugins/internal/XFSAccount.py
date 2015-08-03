# -*- coding: utf-8 -*-

import re
import time
import urlparse

from module.plugins.internal.Account import Account
from module.plugins.internal.Plugin import parse_html_form, set_cookie


class XFSAccount(Account):
    __name__    = "XFSAccount"
    __type__    = "account"
    __version__ = "0.41"
    __status__  = "testing"

    __description__ = """XFileSharing account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg"      , "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com"  )]


    HOSTER_DOMAIN = None
    HOSTER_URL    = None
    LOGIN_URL     = None

    COOKIES = True

    PREMIUM_PATTERN = r'\(Premium only\)'

    VALID_UNTIL_PATTERN = r'Premium.[Aa]ccount expire:.*?(\d{1,2} [\w^_]+ \d{4})'

    TRAFFIC_LEFT_PATTERN = r'Traffic available today:.*?<b>\s*(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</b>'
    TRAFFIC_LEFT_UNIT    = "MB"  #: Used only if no group <U> was found

    LEECH_TRAFFIC_PATTERN = r'Leech Traffic left:<b>.*?(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</b>'
    LEECH_TRAFFIC_UNIT    = "MB"  #: Used only if no group <U> was found

    LOGIN_FAIL_PATTERN = r'Incorrect Login or Password|account was banned|Error<'


    def parse_info(self, user, password, data, req):
        validuntil   = None
        trafficleft  = None
        leechtraffic = None
        premium      = None

        if not self.HOSTER_URL:  #@TODO: Remove in 0.4.10
            return {'validuntil'  : validuntil,
                    'trafficleft' : trafficleft,
                    'leechtraffic': leechtraffic,
                    'premium'     : premium}

        html = self.load(self.HOSTER_URL,
                         get={'op': "my_account"},
                         cookies=self.COOKIES)

        premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.log_debug("Expire date: " + expiredate)

            try:
                validuntil = time.mktime(time.strptime(expiredate, "%d %B %Y"))

            except Exception, e:
                self.log_error(e)

            else:
                self.log_debug("Valid until: %s" % validuntil)

                if validuntil > time.mktime(time.gmtime()):
                    premium     = True
                    trafficleft = -1
                else:
                    premium    = False
                    validuntil = None  #: Registered account type (not premium)
        else:
            self.log_debug("VALID_UNTIL_PATTERN not found")

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

                    trafficleft = self.parse_traffic(size + unit)

            except Exception, e:
                self.log_error(e)
        else:
            self.log_debug("TRAFFIC_LEFT_PATTERN not found")

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

                        leechtraffic += self.parse_traffic(size + unit)

            except Exception, e:
                self.log_error(e)
        else:
            self.log_debug("LEECH_TRAFFIC_PATTERN not found")

        return {'validuntil'  : validuntil,
                'trafficleft' : trafficleft,
                'leechtraffic': leechtraffic,
                'premium'     : premium}


    def login(self, user, password, data, req):
        if self.HOSTER_DOMAIN:
            if not self.HOSTER_URL:
                self.HOSTER_URL = "http://www.%s/" % self.HOSTER_DOMAIN

            if hasattr(self, 'COOKIES'):
                if isinstance(self.COOKIES, list):
                    self.COOKIES.insert((self.HOSTER_DOMAIN, "lang", "english"))
                else:
                    set_cookie(req.cj, self.HOSTER_DOMAIN, "lang", "english")

        if not self.HOSTER_URL:
            self.login_fail(_("Missing HOSTER_URL"))

        if not self.LOGIN_URL:
            self.LOGIN_URL  = urlparse.urljoin(self.HOSTER_URL, "login.html")

        html = self.load(self.LOGIN_URL, cookies=self.COOKIES)

        action, inputs = parse_html_form('name="FL"', html)
        if not inputs:
            inputs = {'op'      : "login",
                      'redirect': self.HOSTER_URL}

        inputs.update({'login'   : user,
                       'password': password})

        if action:
            url = urlparse.urljoin("http://", action)
        else:
            url = self.HOSTER_URL

        html = self.load(url, post=inputs, cookies=self.COOKIES)

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.login_fail()
