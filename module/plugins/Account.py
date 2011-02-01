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
from time import time
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

    def login(self, user, data, req):
        pass

    def _login(self, user, data):
        req = self.getAccountRequest(user)
        try:
            self.login(user, data, req)
        except WrongPassword:
            self.core.log.warning(_("Could not login with %(plugin)s account %(user)s | %(msg)s") % {"plugin": self.__name__, "user": user, "msg": _("Wrong Password")})
            data["valid"] = False

        except Exception, e:
            self.core.log.warning(_("Could not login with %(plugin)s account %(user)s | %(msg)s") % {"plugin" :self.__name__, "user": user, "msg": e})
            data["valid"] = False
            if self.core.debug:
                print_exc()
        finally:
            if req: req.close()
    
    def relogin(self):
        for user, data in self.accounts.iteritems():
            self._login(user, data)
    
    def setAccounts(self, accounts):
        self.accounts = accounts
        for user, data in self.accounts.iteritems():
            self._login(user, data)
            self.infos[user] = {}
    
    def updateAccounts(self, user, password=None, options={}):
        if self.accounts.has_key(user):
            if password:
                self.accounts[user]["password"] = password
            if options:
                self.accounts[user]["options"].update(options)
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
        if force or not self.infos.has_key(name):
            self.core.log.debug("Get %s Account Info for %s" % (self.__name__, name))
            req = self.getAccountRequest(name)

            try:
                infos = self.loadAccountInfo(name, req)
                if not type(infos) == dict:
                    raise Exception("Wrong return format")
            except Exception, e:
                infos = {"error": str(e)}

            if req: req.close()

            self.core.log.debug("Account Info: %s" % str(infos))
            self.infos[name] = infos

        data.update(self.infos[name])
        return data

    def loadAccountInfo(self, name, req=None):
        return {
            "validuntil": None, # -1 for unlimited
            "login": name,
            #"password": self.accounts[name]["password"], #@XXX: security
            "options": self.accounts[name]["options"],
            "valid": self.accounts[name]["valid"],
            "trafficleft": None, # in kb, -1 for unlimited
            "maxtraffic": None,
            "premium": True, #useful for free accounts
            "type": self.__name__,
        }

    def getAllAccounts(self, force=False):
        return [self.getAccountInfo(user, force) for user, data in self.accounts.iteritems()]
    
    def getAccountRequest(self, user=None):
        if not user:
            user, data = self.selectAccount()
        if not user:
            return None

        req = self.core.requestFactory.getRequest(self.__name__, user)
        return req

    def getAccountCookies(self, user=None):
        if not user:
            user, data = self.selectAccount()
        if not user:
            return None

        cj = self.core.requestFactory.getCookieJar(self.__name__, user)
        return cj

    def getAccountData(self, user):
        return self.accounts[user]

    def selectAccount(self):
        """ returns an valid account name and data"""
        usable = []
        for user,data in self.accounts.iteritems():
            if not data["valid"]: continue

            if data["options"].has_key("time") and data["options"]["time"]:
                time_data = ""
                try:
                    time_data = data["options"]["time"][0]
                    start, end = time_data.split("-")
                    if not self.core.compare_time(start.split(":"), end.split(":")):
                        continue
                except:
                    self.core.log.warning(_("Your Time %s has wrong format, use: 1:22-3:44") % time_data)

            if self.infos.has_key(user):
                if self.infos[user].has_key("validuntil"):
                    if self.infos[user]["validuntil"] > 0 and time() > self.infos[user]["validuntil"]:
                        continue
                if self.infos[user].has_key("trafficleft"):
                    if self.infos[user]["trafficleft"] == 0:
                        continue


            usable.append((user, data))

        if not usable: return None, None
        return choice(usable)
    
    def canUse(self):
        return False if self.selectAccount() == (None, None) else True
    
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

    def empty(self, user):
        if self.infos.has_key(user):
            self.core.log.warning(_("%(plugin)s Account %(user)s has not enough traffic, checking again in 30min") % {"plugin" : self.__name__, "user": user})
            self.infos[user].update({"trafficleft": 0})
            self.core.scheduler.addJob(30*60, self.getAccountInfo, [user])

    def expired(self, user):
        if self.infos.has_key(user):
            self.core.log.warning(_("%(plugin)s Account %(user)s is expired, checking again in 1h") % {"plugin" : self.__name__, "user": user})
            self.infos[user].update({"validuntil": time() - 1})
            self.core.scheduler.addJob(60*60, self.getAccountInfo, [user])
