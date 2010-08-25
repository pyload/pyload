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
    
    @author: mkaay
"""

from random import randrange
import re

class Account():
    __name__ = "Account"
    __version__ = "0.2"
    __type__ = "account"
    __description__ = """Account Plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def __init__(self, manager, accounts):
        self.manager = manager
        self.core = manager.core
        self.accounts = {}
        self.register = {}
        self.setAccounts(accounts)
        
    def login(self, user, data):
        pass
    
    def setAccounts(self, accounts):
        self.accounts = accounts
        for user, data in self.accounts.iteritems():
            self.login(user, data)
    
    def updateAccounts(self, user, password, options):
        if self.accounts.has_key(user):
            self.accounts[user]["password"] = password
            self.accounts[user]["options"] = options
        else:
            self.accounts[user] = {"password" : password, "options": options}
            
        self.login(user, self.accounts[user])
    
    def removeAccount(self, user):
        del self.accounts[user]
    
    def getAccountInfo(self, name):
        return {
            "validuntil": None, # -1 for unlimited
            "login": name,
            #"password": self.accounts[name]["password"], #@XXX: security
            "options": self.accounts[name]["options"],
            "trafficleft": None, # -1 for unlimited
            "maxtraffic": None,
            "type": self.__name__,
        }
    
    def getAllAccounts(self):
        return [self.getAccountInfo(user) for user, data in self.accounts.iteritems()]
    
    def getAccountRequest(self, plugin):
        user, data = self.getAccountData(plugin)
        req = self.core.requestFactory.getRequest(self.__name__, user)
        return req
        
    def getAccountData(self, plugin):
        if not len(self.accounts):
            return None
        if not self.register.has_key(plugin):
            account = self.selectAccount(plugin)
            self.register[plugin] = account
        else:
            account = self.register[plugin]
        return account
    
    def selectAccount(self, plugin):
        account = self.accounts.items()[randrange(0, len(self.accounts), 1)]
        return account
    
    def canUse(self):
        return len(self.accounts)
    
    def parseTraffic(self, string): #returns kbyte
        string = string.strip().lower()
        p = re.compile(r"(\d+[\.,]\d+)(.*)")
        m = p.match(string)
        if m:
            traffic = float(m.group(1).replace(",", "."))
            unit = m.group(2).strip()
            if unit == "gb" or unit == "gig" or unit == "gbyte" or unit == "gigabyte":
                traffic *= 1024*1024
            elif unit == "mb" or unit == "megabyte" or unit == "mbyte" or unit == "mib":
                traffic *= 1024
            return traffic
