# -*- coding: utf-8 -*-

from time import time

from module.plugins.Hook import Hook


class MultiHome(Hook):
    __name__ = "MultiHome"
    __type__ = "hook"
    __version__ = "0.11"

    __config__ = [("activated", "bool", "Activated", False),
                  ("interfaces", "str", "Interfaces", "None")]

    __description__ = """Ip address changer"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"


    def setup(self):
        self.register = {}
        self.interfaces = []
        self.parseInterfaces(self.getConfig("interfaces").split(";"))
        if not self.interfaces:
            self.parseInterfaces([self.config['download']['interface']])
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
                self.logDebug("Multihome: using address: " + iface.adress)
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
