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
from shutil import copy

from module.PullEvents import AccountUpdateEvent

ACC_VERSION = 1

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

        self.saveAccounts() # save to add categories to conf

    #----------------------------------------------------------------------
    def getAccountPlugin(self, plugin):
        """get account instance for plugin or None if anonymous"""
        if self.accounts.has_key(plugin):
            if not self.plugins.has_key(plugin):
                self.plugins[plugin] = self.core.pluginManager.getAccountPlugin(plugin)(self, self.accounts[plugin])

            return self.plugins[plugin]
        else:
            return None

    def getAccountPlugins(self):
        """ get all account instances"""
        
        plugins = []
        for plugin in self.accounts.keys():
            plugins.append(self.getAccountPlugin(plugin))
            
        return plugins
    #----------------------------------------------------------------------
    def loadAccounts(self):
        """loads all accounts available"""
        
        if not exists("accounts.conf"):
            f = open("accounts.conf", "wb")
            f.write("version: " + str(ACC_VERSION))
            f.close()
            
        f = open("accounts.conf", "rb")
        content = f.readlines()
        
        version = content.pop(0)
        version = version.split(":")[1].strip()

        if not version or int(version) < ACC_VERSION:
            copy("accounts.conf", "accounts.backup")
            f.close()
            f = open("accounts.conf", "wb")
            f.write("version: " + str(ACC_VERSION))
            f.close()
            self.core.log.warning(_("Account settings deleted, due to new config format."))
            return
            
            
        
        plugin = ""
        name = ""

        for line in content:
            line = line.strip()
            
            if not line: continue
            if line.startswith("#"): continue
            if line.startswith("version"): continue
            
            if line.endswith(":") and line.count(":") == 1:
                plugin = line[:-1]
                self.accounts[plugin] = {}
                
            elif line.startswith("@"):
                option = line[1:].split()
                self.accounts[plugin][name]["options"][option[0]] = True if len(option) < 2 else ([option[1]] if len(option) < 3 else option[1:])
                
            elif ":" in line:
                name, sep, pw = line.partition(":")
                self.accounts[plugin][name] = {"password": pw, "options": {}, "valid": True}
    #----------------------------------------------------------------------
    def saveAccounts(self):
        """save all account information"""
        
        f = open("accounts.conf", "wb")
        f.write("version: " + str(ACC_VERSION) + "\n")
                
        for plugin, accounts in self.accounts.iteritems():
            f.write("\n")
            f.write(plugin+":\n")
            
            for name,data in accounts.iteritems():
                f.write("\n\t%s:%s\n" % (name,data["password"]) )
                for option, values in data["options"].iteritems():
                    f.write("\t@%s %s\n" % (option, " ".join(values)))
                    
        f.close()
            
        
    #----------------------------------------------------------------------
    def initAccountPlugins(self):
        """init names"""
        for name in self.core.pluginManager.getAccountPlugins():
            self.accounts[name] = {}
        
    #----------------------------------------------------------------------
    def updateAccount(self, plugin , user, password=None, options={}):
        """add or update account"""
        if self.accounts.has_key(plugin):
            p = self.getAccountPlugin(plugin)
            p.updateAccounts(user, password, options)
            #since accounts is a ref in plugin self.accounts doesnt need to be updated here
                    
            self.saveAccounts()
            p.getAllAccounts(force=True)
                
    #----------------------------------------------------------------------
    def removeAccount(self, plugin, user):
        """remove account"""
        
        if self.accounts.has_key(plugin):
            p = self.getAccountPlugin(plugin)
            p.removeAccount(user)

            self.saveAccounts()
            p.getAllAccounts(force=True)
    
    def getAccountInfos(self, force=False):
        data = {}
        for p in self.accounts.keys():
            if self.accounts[p]:
                p = self.getAccountPlugin(p)
                data[p.__name__] = p.getAllAccounts(force)
            else:
                data[p] = []
        return data

    def cacheAccountInfos(self):
        self.getAccountInfos()
    
    def sendChange(self):
        e = AccountUpdateEvent()
        self.core.pullManager.addEvent(e)
