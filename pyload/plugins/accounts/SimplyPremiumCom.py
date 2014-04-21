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


class SimplyPremiumCom(Account):
    __name__ = "SimplyPremiumCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Simply-Premium.Com account plugin"""
    __author_name__ = ("EvolutionClip")
    __author_mail__ = ("evolutionclip@live.de")

    def loadAccountInfo(self, user, req):
        json_data = req.load('http://www.simply-premium.com/api/user.php?format=json')
        self.logDebug("JSON data: " + json_data)
        json_data = json_loads(json_data)

        if 'vip' in json_data['result'] and json_data['result']['vip'] == 0:
            return {"premium": False}

        #Time package
        validuntil = float(json_data['result']['timeend'])
        #Traffic package
        # {"trafficleft": int(traffic) / 1024, "validuntil": -1}
        #trafficleft = int(json_data['result']['traffic'] / 1024)

        #return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}
        return {"premium": True, "validuntil": validuntil}

    def login(self, user, data, req):
        req.cj.setCookie("simply-premium.com", "lang", "EN")

        if data['password'] == '' or data['password'] == '0':
            post_data = {"key": user}
        else:
            post_data = {"login_name": user, "login_pass": data["password"]}

        self.html = req.load("http://www.simply-premium.com/login.php", post=post_data)

        if 'logout' not in self.html:
            self.wrongPassword()
