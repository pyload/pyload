# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

import re
from time import mktime, strptime

from pycurl import REFERER

from module.plugins.Account import Account


class FilefactoryCom(Account):
    __name__ = "FilefactoryCom"
    __version__ = "0.14"
    __type__ = "account"
    __description__ = """filefactory.com account plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    VALID_UNTIL_PATTERN = r'Premium valid until: <strong>(?P<d>\d{1,2})\w{1,2} (?P<m>\w{3}), (?P<y>\d{4})</strong>'

    def loadAccountInfo(self, user, req):
        html = req.load("http://www.filefactory.com/account/")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            premium = True
            validuntil = re.sub(self.VALID_UNTIL_PATTERN, '\g<d> \g<m> \g<y>', m.group(0))
            validuntil = mktime(strptime(validuntil, "%d %b %Y"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def login(self, user, data, req):
        req.http.c.setopt(REFERER, "http://www.filefactory.com/member/login.php")

        html = req.load("http://www.filefactory.com/member/signin.php", post={
            "loginEmail": user,
            "loginPassword": data["password"],
            "Submit": "Sign In"})

        if req.lastEffectiveURL != "http://www.filefactory.com/account/":
            self.wrongPassword()
