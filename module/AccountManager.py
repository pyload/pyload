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

########################################################################
class AccountManager():
	"""manages all accounts"""

	#----------------------------------------------------------------------
	def __init__(self, core):
		"""Constructor"""
		
		self.core = core
		
		self.accounts = {} # key = ( plugin )
		
		self.loadAccounts()
		
	#----------------------------------------------------------------------
	def getAccount(self, plugin):
		"""get account instance for plugin or None if anonymous"""
		#@TODO ...
		return None
		
    
	#----------------------------------------------------------------------
	def loadAccounts(self):
		"""loads all accounts available"""
		pass
		
	#----------------------------------------------------------------------
	def saveAccounts(self):
		"""save all account information"""
		pass
		
	