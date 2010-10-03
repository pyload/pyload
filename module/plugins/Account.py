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

import re
from random import choice
from traceback import print_exc

class WrongPassword(Exception):
    pass

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
        self.infos = {} # cache for account information
        self.setAccounts(accounts)

    def login(self, user, data):
        pass

    def _login(self, user, data):
        try:
            self.login(user, data)
        except WrongPassword:
            self.core.log.warning(_("Could not login with account %s | %s") % (user, _("Wrong Password")))
            data["valid"] = False

        except Exception, e:
            self.core.log.warning(_("Could not login with account %s | %s") % (user, e))
            data["valid"] = False
            if self.core.debug:
                print_exc()

    def setAccounts(self, accounts):
        self.accounts = accounts
        for user, data in self.accounts.iteritems():
            self._login(user, data)
    
    def updateAccounts(self, user, password, options):
        if self.accounts.has_key(user):
            self.accounts[user]["password"] = password
            self.accounts[user]["options"] = options
            self.accounts[user]["valid"] = True
        else:
            self.accounts[user] = {"password" : password, "options": options, "valid": True}

        self._login(user, self.accounts[user])
    
    def removeAccount(self, user):
        if self.accounts.has_key(user):
            del self.accounts[user]
        if self.infos.has_key(user):
            del self.infos[user]
    
    def getAccountInfo(self, name, force=False):
        """ return dict with infos, do not overwrite this method! """
        data = Account.loadAccountInfo(self, name)
        if not self.infos.has_key(name) or force:
            self.core.log.debug("Get Account Info for %s" % name)
            try:
                infos = self.loadAccountInfo(name)
            except Exception, e:
                infos = {"error": str(e)}
            self.core.log.debug("Account Info: %s" % str(infos))
            self.infos[name] = infos

        data.update(self.infos[name])
        return data

    def loadAccountInfo(self, name):
        return {
            "validuntil": None, # -1 for unlimited
            "login": name,
            #"password": self.accounts[name]["password"], #@XXX: security
            "options": self.accounts[name]["options"],
            "valid": self.accounts[name]["valid"],
            "trafficleft": None, # -1 for unlimited
            "maxtraffic": None,
            "type": self.__name__,
        }

    def getAllAccounts(self, force=False):
        return [self.getAccountInfo(user, force) for user, data in self.accounts.iteritems()]
    
    def getAccountRequest(self, user=None):
        if not user:
            user, data = self.selectAccount()
        req = self.core.requestFactory.getRequest(self.__name__, user)
        return req

    def getAccountCookies(self, user=None):
        if not user:
            user, data = self.selectAccount()
        cj = self.core.requestFactory.getCookieJar(self.__name__, user)
        return cj

    def getAccountData(self, user):
        return self.accounts[user]

    def selectAccount(self):
        """ returns an valid and account name"""
        usable = []
        for user,data in self.accounts.iteritems():
            if not data["valid"]: continue
            for option, value in data["options"]:
                pass
                #@TODO comparate time option

            usable.append((user, data))

        if not usable: return None
        return choice(usable)
    
    def canUse(self):
        return True if self.selectAccount() else False
    
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

    def wrongPassword(self):
        raise WrongPassword
