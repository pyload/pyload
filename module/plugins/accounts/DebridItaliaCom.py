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
import time

from module.plugins.Account import Account


class DebridItaliaCom(Account):
    __name__ = "DebridItaliaCom"
    __version__ = "0.1"
    __type__ = "account"

    __description__ = """Debriditalia.com account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    WALID_UNTIL_PATTERN = r"Premium valid till: (?P<D>[^|]+) \|"


    def loadAccountInfo(self, user, req):
        if 'Account premium not activated' in self.html:
            return {"premium": False, "validuntil": None, "trafficleft": None}

        m = re.search(self.WALID_UNTIL_PATTERN, self.html)
        if m:
            validuntil = int(time.mktime(time.strptime(m.group('D'), "%d/%m/%Y %H:%M")))
            return {"premium": True, "validuntil": validuntil, "trafficleft": -1}
        else:
            self.logError('Unable to retrieve account information - Plugin may be out of date')

    def login(self, user, data, req):
        self.html = req.load("http://debriditalia.com/login.php",
                             get={"u": user, "p": data['password']})
        if 'NO' in self.html:
            self.wrongPassword()
