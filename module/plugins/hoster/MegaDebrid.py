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
from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads


class MegaDebrid(Hoster):
	__name__ = "MegaDebrid"
	__version__ = "0.1"
	__type__ = "hoster"
	__pattern__ = r'^https?://(?:w{3}\d+\.mega-debrid.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[^/]+/.+$'
	__description__ = """mega-debrid.eu hoster plugin"""
	__author_name__ = "D.Ducatel"
	__author_mail__ = "dducatel@je-geek.fr"

	# Define the base URL of MegaDebrid api
	API_URL = "https://www.mega-debrid.eu/api.php"

	def process(self, pyfile):
		if re.match(self.__pattern__, pyfile.url):
			new_url = pyfile.url
		elif not self.account:
			self.exitOnFail(_("Please enter your %s account or deactivate this plugin") % "Mega-debrid.eu")
		else:

			if not self.connectToApi() :
				self.exitOnFail(_("Impossible to connect to %s") % "Mega-debrid.eu")

			self.logDebug("Old URL: %s" % pyfile.url)
			new_url = self.debridLink(pyfile.url)
		
			if new_url == pyfile.url:
				self.exitOnFail(_("Impossible to debrid %s")% new_url )

			self.logDebug("New URL: " + new_url)
			
		self.download(new_url, disposition=True)


	def connectToApi(self):
		"""
		Connexion to the mega-debrid API 
		Return True if succeed
		"""
		user, data = self.account.selectAccount()
		url = "{0}?action=connectUser&login={1}&password={2}".format(self.API_URL, user, data['password'])
		response = json_loads(self.req.load(url))
		
		if response["response_code"] == "ok" :
			self.token = response["token"]
			return True
		else :
			return False
		

	def debridLink(self, linkToDebrid):
		"""
		Debrid a link
		Return The debrided link if succeed or original link if fail
		"""
		params = { "link" : linkToDebrid }
		url = "{0}?action=getLink&token={1}".format(self.API_URL, self.token)
		response = json_loads(self.req.load(url, post=params))
		if response["response_code"] == "ok" :
			debridedLink = response["debridLink"][1:-1]
			return debridedLink
		else :
			return linkToDebrid

	def exitOnFail(self, msg):
		"""
		exit the plugin on fail case
		And display the reason of this failure
		"""
		if self.getConfig("unloadFailing"):
			self.logError(msg)
			self.resetAccount()
		else:
			self.fail(msg)
