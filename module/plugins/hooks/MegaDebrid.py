# -*- coding: utf-8 -*-

from module.plugins.Hook import Hook
import urllib2
import urllib
import json


class MegaDebrid(Hook):
	"""
	This plugin can debrid a link managed by MegaDebrid.
	For using it, you must have a MageDrebid account
	"""
	__name__ = "MegaDebrid"
	__version__ = "0.1"
	__description__ = "Debrid link with Mega-Debrid.eu"
	__config__ = [ ("login" , "str" , "login"  , "" ), ("password" , "password" , "password"  , "" ) ]
	__threaded__ = ["linksAdded"]
	__author_name__ = ("D.Ducatel")
	__author_mail__ = ("dducatel@je-geek.fr")

	# Define the callback on HookManager event
	event_map = {"linksAdded" : "linksAddedCallback"}
	
	# Define the base URL of MegaDebrid api
	API_URL = "https://www.mega-debrid.eu/api.php"

	def linksAddedCallback(self, links, pid):
		"""
		A callback on linksAdded event
		"""
		if self.connectToApi() == False :
			return links

		linksDebrided = []
		for linkToDebrid in links :
			debridedLink = self.debridLink(linkToDebrid)
			linksDebrided.append(debridedLink)
			links.remove(linkToDebrid)
		
		for link in linksDebrided :
			links.append(link)

	def connectToApi(self):
		"""
		Connexion to the mega-debrid API 
		Return True if succeed
		"""
		login = self.getConfig("login")
		password = self.getConfig("password")

		url = "{0}?action=connectUser&login={1}&password={2}".format(self.API_URL, login, password)
		response = json.loads(urllib2.urlopen(url).read())
		
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
		params = urllib.urlencode({ "link" : linkToDebrid })
		url = "{0}?action=getLink&token={1}".format(self.API_URL, self.token)
		response = json.loads(urllib2.urlopen(url, params).read())

		if response["response_code"] == "ok" :
			debridedLink = response["debridLink"][1:-1]
			strLogInfo = "The link {0} was debrided in {1}".format(linkToDebrid, debridedLink)
			self.logInfo(strLogInfo)
			return debridedLink
		else :
			strLogWarning = "Impossible to debrid {0}".format(linkToDebrid)
			self.logWarning(strLogWarning)
			return linkToDebrid

