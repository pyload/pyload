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
import string

class HellspyCz(Account):
    __name__ = "HellspyCz"
    __version__ = "0.2"
    __type__ = "account"
    __description__ = """hellspy.cz account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    CREDIT_LEFT_PATTERN = r'<strong>Credits: </strong>\s*(\d+)'
    WRONG_PASSWORD_PATTERN = r'<p class="block-error-3 marg-tb-050">\s*Wrong user or password was entered<br />'

    phpsessid = ''

    def loadAccountInfo(self, user, req):
        cj = self.getAccountCookies(user)
        cj.setCookie(".hellspy.com", "PHPSESSID", self.phpsessid)

        html = req.load("http://www.hellspy.com/")

        found = re.search(self.CREDIT_LEFT_PATTERN, html)
        if found is None:
            credits = 0
        else:
            credits = int(found.group(1)) * 1024

        return {"validuntil": -1, "trafficleft": credits}

    def login(self, user, data,req):
        header = req.load('http://www.hellspy.com/', just_header = True)
        self.phpsessid = re.search(r'PHPSESSID=(\w+)', header).group(1)       
        self.logDebug("PHPSESSID:" + self.phpsessid)
        
        html = req.load("http://www.hellspy.com/--%s-" % self.phpsessid)

        html = req.load("http://www.hell-share.com/user/login/?do=apiLoginForm-submit&api_hash=hellspy_iq&user_hash=%s" % self.phpsessid, post={
                "login": "1",
                "password": data["password"],
                "username": user,
                "redir_url":	'http://www.hellspy.com/?do=loginBox-login',
                "permanent_login": "1"
                })

        cj = self.getAccountCookies(user)
        cj.setCookie(".hellspy.com", "PHPSESSID", self.phpsessid)

        if not re.search(self.CREDIT_LEFT_PATTERN, html):
            self.wrongPassword()