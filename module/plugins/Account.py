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
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """Account Plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def __init__(self, manager):
        self.manager = manager
        self.core = manager.core
        self.configParser = self.core.parser_plugins
        
        self.accounts = []
        self.register = {}
        self.loadAccounts()
    
    def login(self):
        pass
    
    def getAccountInfo(self, name):
        return {
            "validuntil": None,
            "login": None,
            "trafficleft": None
        }
    
    def getAccountRequest(self, plugin):
        account = self.getAccountData(plugin)
        req = self.core.requestFactory.getRequest(self.__name__, account[0])
        return req
    
    def loadAccounts(self):
        usernames = self.configParser.get(self.__name__, "username")
        passwords = self.configParser.get(self.__name__, "password")
        
        data = zip(usernames.split("\n"), passwords.split("\n"))
        self.accounts = []
        for acc in data:
            t = (acc[0].strip(), acc[1].strip())
            if t[0] and t[1]:
                self.accounts.append(t)
        
        self.login()
    
    def getAccountData(self, plugin):
        if not len(self.accounts):
            return None
        if not self.register.has_key(plugin):
            account = self.accounts[randrange(0, len(self.accounts), 1)]
        else:
            account = self.register[plugin]
        return account
    
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
