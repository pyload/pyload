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

from module.plugins.Addon import Addon
from time import time

class MultiHome(Addon):
    __name__ = "MultiHome"
    __version__ = "0.1"
    __description__ = """ip address changer"""
    __config__ = [ ("activated", "bool", "Activated" , "False"),
                   ("interfaces", "str", "Interfaces" , "None") ]
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def setup(self):
        self.register = {}
        self.interfaces = []
        self.parseInterfaces(self.getConfig("interfaces").split(";"))
        if not self.interfaces:
            self.parseInterfaces([self.config["download"]["interface"]])
            self.setConfig("interfaces", self.toConfig())
    
    def toConfig(self):
        return ";".join([i.adress for i in self.interfaces])
    
    def parseInterfaces(self, interfaces):
        for interface in interfaces:
            if not interface or str(interface).lower() == "none":
                continue
            self.interfaces.append(Interface(interface))
    
    def coreReady(self):
        requestFactory = self.core.requestFactory
        oldGetRequest = requestFactory.getRequest
        def getRequest(pluginName, account=None):
            iface = self.bestInterface(pluginName, account)
            if iface:
                iface.useFor(pluginName, account)
                requestFactory.iface = lambda: iface.adress
                self.log.debug("Multihome: using address: "+iface.adress)
            return oldGetRequest(pluginName, account)
        requestFactory.getRequest = getRequest
    
    def bestInterface(self, pluginName, account):
        best = None
        for interface in self.interfaces:
            if not best or interface.lastPluginAccess(pluginName, account) < best.lastPluginAccess(pluginName, account):
                best = interface
        return best

class Interface(object):
    def __init__(self, adress):
        self.adress = adress
        self.history = {}
    
    def lastPluginAccess(self, pluginName, account):
        if (pluginName, account) in self.history:
            return self.history[(pluginName, account)]
        return 0
    
    def useFor(self, pluginName, account):
        self.history[(pluginName, account)] = time()
    
    def __repr__(self):
        return "<Interface - %s>" % self.adress
