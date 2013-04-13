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

from time import time

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class MultiDebridCom(Account):
    __name__ = "MultiDebridCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Multi-debrid.com account plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def loadAccountInfo(self, user, req):
        if 'days_left' in self.json_data:
            validuntil = int(time() + self.json_data['days_left'] * 86400)
            return {"premium": True, "validuntil": validuntil, "trafficleft": -1}
        else:
            self.logError('Unable to get account information')

    def login(self, user, data, req):
        # Password to use is the API-Password written in http://multi-debrid.com/myaccount
        self.html = req.load("http://multi-debrid.com/api.php",
                             get={"user": user, "pass": data["password"]})
        self.logDebug('JSON data: ' + self.html)
        self.json_data = json_loads(self.html)
        if self.json_data['status'] != 'ok':
            self.logError('Invalid login. The password to use is the API-Password you find in your "My Account" page')
            self.wrongPassword()
