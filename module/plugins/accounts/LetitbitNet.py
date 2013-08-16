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
# from module.common.json_layer import json_loads, json_dumps


class LetitbitNet(Account):
    __name__ = "LetitbitNet"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Letitbit.net account plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def loadAccountInfo(self, user, req):
        ## DISABLED BECAUSE IT GET 'key exausted' EVEN IF VALID ##
        # api_key = self.accounts[user]['password']
        # json_data = [api_key, ["key/info"]]
        # api_rep = req.load('http://api.letitbit.net/json', post={'r': json_dumps(json_data)})
        # self.logDebug('API Key Info: ' + api_rep)
        # api_rep = json_loads(api_rep)
        #
        # if api_rep['status'] == 'FAIL':
        #     self.logWarning(api_rep['data'])
        #     return {'valid': False, 'premium': False}

        return {"premium": True}

    def login(self, user, data, req):
        # API_KEY is the username and the PREMIUM_KEY is the password
        self.logInfo('You must use your API KEY as username and the PREMIUM KEY as password.')
