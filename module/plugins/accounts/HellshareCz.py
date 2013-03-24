# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

from module.plugins.Account import Account
import re
import time

class HellshareCz(Account):
    __name__ = "HellshareCz"
    __version__ = "0.14"
    __type__ = "account"
    __description__ = """hellshare.cz account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    CREDIT_LEFT_PATTERN = r'<div class="credit-link">\s*<table>\s*<tr>\s*<th>(\d+|\d\d\.\d\d\.)</th>'

    def loadAccountInfo(self, user, req):
        self.relogin(user)
        html = req.load("http://www.hellshare.com/")

        found = re.search(self.CREDIT_LEFT_PATTERN, html)
        if found is None:
            trafficleft = None
            validuntil = None
            premium = False
        else:
            credit = found.group(1)
            premium = True
            try:
                if "." in credit:
                    #Time-based account
                    vt = [int(x) for x in credit.split('.')[:2]]
                    lt = time.localtime()
                    year = lt.tm_year + int(vt[1] < lt.tm_mon or (vt[1] == lt.tm_mon and vt[0] < lt.tm_mday))
                    validuntil = time.mktime(time.strptime("%s%d 23:59:59" % (credit,year), "%d.%m.%Y %H:%M:%S")) 
                    trafficleft = -1
                else:
                    #Traffic-based account
                    trafficleft = int(credit) * 1024
                    validuntil = -1
            except Exception, e:
                self.logError('Unable to parse credit info', e)
                validuntil = -1
                trafficleft = -1

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}

    def login(self, user, data, req):
        html = req.load('http://www.hellshare.com/')
        if req.lastEffectiveURL != 'http://www.hellshare.com/':
            #Switch to English
            self.logDebug('Switch lang - URL: %s' % req.lastEffectiveURL)
            json = req.load("%s?do=locRouter-show" % req.lastEffectiveURL)
            hash = re.search(r"(--[0-9a-f]+-)", json).group(1)
            self.logDebug('Switch lang - HASH: %s' % hash)
            html = req.load('http://www.hellshare.com/%s/' % hash)

        if re.search(self.CREDIT_LEFT_PATTERN, html):
            self.logDebug('Already logged in')
            return

        html = req.load('http://www.hellshare.com/login?do=loginForm-submit', post={
                "login": "Log in",
                "password": data["password"],
                "username": user,
                "perm_login": "on"
                })

        if "<p>You input a wrong user name or wrong password</p>" in html:
            self.wrongPassword()