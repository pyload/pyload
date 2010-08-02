#!/usr/bin/env python
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

    @author: RaNaN
"""

from os.path import exists

########################################################################
class AccountManager():
	"""manages all accounts"""

	#----------------------------------------------------------------------
	def __init__(self, core):
		"""Constructor"""
		
		self.core = core
		
		self.accounts = {} # key = ( plugin )
		self.plugins = {}
		
		self.initAccountPlugins()
		self.loadAccounts()
		
	#----------------------------------------------------------------------
	def getAccountPlugin(self, plugin):
		"""get account instance for plugin or None if anonymous"""
		if self.accounts.has_key(plugin):
			if not self.plugins.has_key(plugin):
				self.plugins[plugin] = self.core.pluginManager.getAccountPlugin(plugin)(self, self.accounts[plugin])
				
			return self.plugins[plugin]
		else:
			return None
		
    
	#----------------------------------------------------------------------
	def loadAccounts(self):
		"""loads all accounts available"""
		
		if not exists("accounts.conf"):
			f = open("accounts.conf", "wb")
			f.close()
			
		f = open("accounts.conf", "rb")
		content = f.readlines()
		
		plugin = ""
		account = ""

		for line in content:
			line = line.strip()
			
			if not line: continue
			if line.startswith("#"): continue
			
			if line.endswith(":"):
				plugin = line[:-1]
				self.accounts[plugin] = {}
				
			elif line.startswith("@"):
				option = line[1:].split()
				self.accounts[plugin][name]["options"].append(tuple(option))
				
			elif ":" in line:
				name, pw = line.split(":")[:]
				self.accounts[plugin][name] = {"pw": pw, "options":  []}
		
		
		
	#----------------------------------------------------------------------
	def saveAccounts(self):
		"""save all account information"""
		pass
		
	#----------------------------------------------------------------------
	def initAccountPlugins(self):
		"""init names"""
		for name in self.core.pluginManager.getAccountPlugins():
			self.accounts[name] = {}
		