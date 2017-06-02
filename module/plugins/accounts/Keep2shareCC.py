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

    @author: aeronaut
"""

from module.plugins.Account import Account
import re
from time import strptime, mktime
import time

class Keep2shareCC(Account):
    __name__ = "Keep2shareCC"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """Keep2shareCC account plugin"""
    __author_name__ = ("aeronaut")
    __author_mail__ = ("aeronaut@pianoguy.de")

    def loadAccountInfo(self, user, req):
        req.load("http://keep2share.cc/")
        src = req.load("http://keep2share.cc/site/profile.html").replace("\n", "")
        validuntil = re.search(r"Premium expires: <b>(.*?)</b>", src)
        if validuntil:
                validuntil = mktime(strptime(validuntil.group(1), "%Y.%m.%d"))
                if validuntil > mktime(time.gmtime()):
                        premium = True
                        trafficleft = re.search(r'Available traffic \(today\):<b><a href="/user/statistic.html">(.*?)</a>', src).group(1)
                        v,u = trafficleft.split( )
                        vi = int(float(v))
                        if u == "GB":
                                vi = vi * 1024 * 1024
                        elif u == "MB":
                                vi = vi * 1024

                        trafficleft = vi
                        premium = True
        else:
             validuntil = -1
             trafficleft = None
             premium = False
        tmp = {"validuntil": validuntil, "trafficleft": trafficleft, "premium" : premium}
        return tmp

    def login(self, user, data, req):
        req.load("http://keep2share.cc/")
        req.cj.setCookie("keep2share.cc", "lang", "en")
        page = req.load("http://keep2share.cc/login.html", post={"LoginForm[username]": user, "LoginForm[password]": data["password"]})
        if "Please fix the following input errors" in page:
                self.wrongPassword()