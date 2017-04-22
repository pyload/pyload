# -*- coding: utf-8 -*-

import re
import time
import urlparse

from .misc import parse_html_form, parse_time, set_cookie
from .Account import Account


class XFSAccount(Account):
    __name__ = "XFSAccount"
    __type__ = "account"
    __version__ = "0.59"
    __status__ = "stable"

    __config__ = [("activated", "bool", "Activated", True),
                  ("multi", "bool", "Multi-hoster", True),
                  ("multi_mode", "all;listed;unlisted", "Hosters to use", "all"),
                  ("multi_list", "str", "Hoster list (comma separated)", ""),
                  ("multi_interval", "int", "Reload interval in hours", 12)]

    __description__ = """XFileSharing account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = None
    PLUGIN_URL = None
    LOGIN_URL = None

    COOKIES = True

    PREMIUM_PATTERN = r'\(Premium only\)'

    VALID_UNTIL_PATTERN = r'Premium.[Aa]ccount expire:.*?(\d{1,2} [\w^_]+ \d{4})'

    TRAFFIC_LEFT_PATTERN = r'Traffic available today:.*?<b>\s*(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</b>'
    TRAFFIC_LEFT_UNIT = "MB"  #: Used only if no group <U> was found

    LEECH_TRAFFIC_PATTERN = r'Leech Traffic left:<b>.*?(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</b>'
    LEECH_TRAFFIC_UNIT = "MB"  #: Used only if no group <U> was found

    LOGIN_FAIL_PATTERN = r'Incorrect Login or Password|account was banned|Error<'
    LOGIN_BAN_PATTERN = r'>(Your IP.+?)<a'
    LOGIN_SKIP_PATTERN = r'op=logout'

    def _set_xfs_cookie(self):
        cookie = (self.PLUGIN_DOMAIN, "lang", "english")
        if isinstance(self.COOKIES, list) and cookie not in self.COOKIES:
            self.COOKIES.insert(cookie)
        else:
            set_cookie(self.req.cj, *cookie)

    def setup(self):
        if not self.PLUGIN_DOMAIN:
            self.fail_login(_("Missing PLUGIN DOMAIN"))

        if not self.PLUGIN_URL:
            self.PLUGIN_URL = "http://www.%s/" % self.PLUGIN_DOMAIN

        if not self.LOGIN_URL:
            self.LOGIN_URL = urlparse.urljoin(self.PLUGIN_URL, "login.html")

        if self.COOKIES:
            self._set_xfs_cookie()

    #@TODO: Implement default grab_hosters routine
    # def grab_hosters(self, user, password, data):
        # pass

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        leechtraffic = None
        premium = None

        if not self.PLUGIN_URL:  # @TODO: Remove in 0.4.10
            return

        self.data = self.load(self.PLUGIN_URL,
                              get={'op': "my_account"},
                              cookies=self.COOKIES)

        premium = True if re.search(self.PREMIUM_PATTERN, self.data) else False

        m = re.search(self.VALID_UNTIL_PATTERN, self.data)
        if m is not None:
            expiredate = m.group(1).strip()
            self.log_debug("Expire date: " + expiredate)

            try:
                validuntil = time.mktime(time.strptime(expiredate, "%d %B %Y"))

            except Exception, e:
                self.log_error(e)

            else:
                self.log_debug("Valid until: %s" % validuntil)

                if validuntil > time.mktime(time.gmtime()):
                    premium = True
                    trafficleft = -1
                else:
                    premium = False
                    validuntil = None  #: Registered account type (not premium)
        else:
            self.log_debug("VALID UNTIL PATTERN not found")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, self.data)
        if m is not None:
            try:
                traffic = m.groupdict()
                size = traffic['S']

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
            self.log_debug("TRAFFIC LEFT PATTERN not found")

        leech = [
            m.groupdict() for m in re.finditer(
                self.LEECH_TRAFFIC_PATTERN,
                self.data)]
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
            self.log_debug("LEECH TRAFFIC PATTERN not found")

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'leechtraffic': leechtraffic,
                'premium': premium}

    def signin(self, user, password, data):
        self.data = self.load(self.LOGIN_URL, cookies=self.COOKIES)

        if re.search(self.LOGIN_SKIP_PATTERN, self.data):
            self.skip_login()

        action, inputs = parse_html_form('name="FL"', self.data)
        if not inputs:
            inputs = {'op': "login",
                      'redirect': self.PLUGIN_URL}

        inputs.update({'login': user,
                       'password': password})

        if action:
            url = urlparse.urljoin("http://", action)
        else:
            url = self.LOGIN_URL

        self.data = self.load(url, post=inputs, cookies=self.COOKIES)

        self.check_errors()

    def check_errors(self):
        self.log_info(_("Checking for link errors..."))

        if not self.data:
            self.log_warning(_("No data to check"))
            return

        m = re.search(self.LOGIN_BAN_PATTERN, self.data)
        if m is not None:
            try:
                errmsg = m.group(1)

            except (AttributeError, IndexError):
                errmsg = m.group(0)

            finally:
                errmsg = re.sub(r'<.*?>', " ", errmsg.strip())

            new_timeout = parse_time(errmsg)
            if new_timeout > self.timeout:
                self.timeout = new_timeout

            self.fail_login(errmsg)

        m = re.search(self.LOGIN_FAIL_PATTERN, self.data)
        if m is not None:
            try:
                errmsg = m.group(1)

            except (AttributeError, IndexError):
                errmsg = m.group(0)

            finally:
                errmsg = re.sub(r'<.*?>', " ", errmsg.strip())

            self.timeout = self.LOGIN_TIMEOUT
            self.fail_login(errmsg)

        self.log_info(_("No errors found"))
