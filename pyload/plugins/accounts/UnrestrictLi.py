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

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class UnrestrictLi(Account):
    __name__ = "UnrestrictLi"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """Unrestrict.li account plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def loadAccountInfo(self, user, req):
        json_data = req.load('http://unrestrict.li/api/jdownloader/user.php?format=json')
        self.logDebug("JSON data: " + json_data)
        json_data = json_loads(json_data)

        if 'vip' in json_data['result'] and json_data['result']['vip'] == 0:
            return {"premium": False}

        validuntil = json_data['result']['expires']
        trafficleft = int(json_data['result']['traffic'] / 1024)

        return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}

    def login(self, user, data, req):
        html = req.load("https://unrestrict.li/sign_in")

        if 'solvemedia' in html:
            self.logError("A Captcha is required. Go to http://unrestrict.li/sign_in and login, then retry")
            return

        self.html = req.load("https://unrestrict.li/sign_in",
                             post={"username": user, "password": data["password"], "signin": "Sign in"})

        if 'sign_out' not in self.html:
            self.wrongPassword()
