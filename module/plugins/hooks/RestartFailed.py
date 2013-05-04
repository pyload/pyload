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

	@author: vuolter
"""

from module.plugins.Hook import Hook
import time

class RestartFailed(Hook):
	__name__        = "RestartFailed"
	__version__     = "0.3"
	__description__ = "Restart failed packages according to defined rules"
	__config__      = [ ("activated", "bool", "Activated" , "True"),
						("on_downloadFailed", "bool", "Restart if downloads fails" , "True"),
						("downloadFailed_number", "int", "Only restart when failed downloads are more than", "5"),
						("downloadFailed_interval", "int", "Only restart when elapsed time since last one is (min)", "10"),
						("on_packageFinished", "bool", "Restart when package finished" , "True")
						("on_reconnect", "bool", "Restart after reconnected" , "True") ]
	__author_name__ = ("vuolter")
	__author_mail__ = ("vuolter@gmail.com")

	failed = 0
	lastime = 0
	
	def checkInterval(self, interval):
		interval *= 60
		if now = time() >= lastime + interval :
			lastime = now
			return True
		else
			return False
	
	def downloadFailed(self, pyfile):
		if not self.getConfig("on_downloadFailed"):
			failed = 0
			return
		if failed > number = self.getConfig("downloadFailed_number") 
		and checkInterval(interval = self.getConfig("downloadFailed_interval")) :
			self.core.api.restartFailed()
			self.logDebug(self.__name__ + ": executed after " + failed + " downloads failed")
			failed = 0
		else
			++failed
			
	def packageFinished(self, pypack):
		if not self.getConfig("on_packageFinished"):
			return
		self.core.api.restartFailed()
		self.logDebug(self.__name__ + ": executed after one package finished")
	
	def afterReconnecting(self, ip):
		if not self.getConfig("on_reconnect"):
			return
		self.core.api.restartFailed()
		self.logDebug(self.__name__ + ": executed after reconnecting")
