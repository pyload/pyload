# -*- coding: utf-8 -*-

import re
import time

from ..internal.Account import Account


class HellshareCz(Account):
    __name__ = "HellshareCz"
    __type__ = "account"
    __version__ = "0.26"
    __status__ = "testing"

    __description__ = """Hellshare.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    CREDIT_LEFT_PATTERN = r'<div class="credit-link">\s*<table>\s*<tr>\s*<th>(\d+|\d\d\.\d\d\.)</th>'

    def grab_info(self, user, password, data):
        html = self.load("http://www.hellshare.com/")

        m = re.search(self.CREDIT_LEFT_PATTERN, html)
        if m is None:
            trafficleft = None
            validuntil = None
            premium = False
        else:
            credit = m.group(1)
            premium = True
            try:
                if "." in credit:
                    #: Time-based account
                    vt = [int(x) for x in credit.split('.')[:2]]
                    lt = time.localtime()
                    year = lt.tm_year + \
                        int(vt[1] < lt.tm_mon or (
                            vt[1] == lt.tm_mon and vt[0] < lt.tm_mday))
                    validuntil = time.mktime(
                        time.strptime(
                            "%s%d 23:59:59" %
                            (credit, year), "%d.%m.%Y %H:%M:%S"))
                    trafficleft = -1
                else:
                    #: Traffic-based account
                    trafficleft = self.parse_traffic(credit, "MB")
                    validuntil = -1

            except Exception, e:
                self.log_error(_("Unable to parse credit info"), e)
                validuntil = -1
                trafficleft = -1

        return {'validuntil': validuntil,
                'trafficleft': trafficleft, 'premium': premium}

    def signin(self, user, password, data):
        html = self.load('http://www.hellshare.com/')
        if self.req.lastEffectiveURL != 'http://www.hellshare.com/':
            #: Switch to English
            self.log_debug("Switch lang - URL: %s" % self.req.lastEffectiveURL)

            json = self.load(
                "%s?do=locRouter-show" %
                self.req.lastEffectiveURL)
            hash = re.search(r'(--[0-9a-f]+\-)', json).group(1)

            self.log_debug("Switch lang - HASH: %s" % hash)

            html = self.load('http://www.hellshare.com/%s/' % hash)

        if re.search(self.CREDIT_LEFT_PATTERN, html):
            self.log_debug("Already logged in")
            return

        html = self.load("https://www.hellshare.com/login",
                         get={'do': "loginForm-submit"},
                         post={'login': "Log in",
                               'password': password,
                               'username': user,
                               'perm_login': "on"})

        if "<p>You input a wrong user name or wrong password</p>" in html:
            self.fail_login()
