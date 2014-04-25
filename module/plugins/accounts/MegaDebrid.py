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


class MegaDebrid(Account):
	__name__ = "MegaDebrid"
	__version__ = "0.1"
	__type__ = "account"
	__description__ = """mega-debrid.eu account plugin"""
	__author_name__ = "D.Ducatel"
	__author_mail__ = "dducatel@je-geek.fr"

	# Define the base URL of MegaDebrid api
	API_URL = "https://www.mega-debrid.eu/api.php"

	def loadAccountInfo(self, user, req):

		data = self.getAccountData(user)
		url = "{0}?action=connectUser&login={1}&password={2}".format(self.API_URL, user, data["password"])
		jsonResponse = req.load(url)
		response = json_loads(jsonResponse)
		
		if response["response_code"] == "ok" :
			return {"premium": True, "validuntil": float(response["vip_end"]), "status" : True}
		else:
			self.logError(response)
			return {"status" : False, "premium": False}

	def login(self, user, data, req):

		url = "{0}?action=connectUser&login={1}&password={2}".format(self.API_URL, user, data["password"])
		response = json_loads(req.load(url))
		if response["response_code"] != "ok" :
			 self.wrongPassword()
