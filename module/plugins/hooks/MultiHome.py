# -*- coding: utf-8 -*-

import time

from module.plugins.internal.Addon import Addon


class MultiHome(Addon):
    __name__    = "MultiHome"
    __type__    = "hook"
    __version__ = "0.14"
    __status__  = "testing"

    __config__ = [("interfaces", "str", "Interfaces", "None")]

    __description__ = """IP address changer"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    def init(self):
        self.register   = {}
        self.interfaces = []

        self.parse_interfaces(self.get_config('interfaces').split(";"))

        if not self.interfaces:
            self.parse_interfaces([self.pyload.config.get("download", "interface")])
            self.set_config("interfaces", self.to_config())


    def to_config(self):
        return ";".join(i.adress for i in self.interfaces)


    def parse_interfaces(self, interfaces):
        for interface in interfaces:
            if not interface or str(interface).lower() == "none":
                continue
            self.interfaces.append(Interface(interface))


    def activate(self):
        requestFactory = self.pyload.requestFactory
        oldGetRequest = requestFactory.getRequest


        def get_request(pluginName, account=None):
            iface = self.best_interface(pluginName, account)
            if iface:
                iface.useFor(pluginName, account)
                requestFactory.iface = lambda: iface.adress
                self.log_debug("Using address", iface.adress)
            return oldGetRequest(pluginName, account)

        requestFactory.getRequest = get_request


    def best_interface(self, pluginName, account):
        best = None
        for interface in self.interfaces:
            if not best or interface.lastPluginAccess(pluginName, account) < best.lastPluginAccess(pluginName, account):
                best = interface
        return best


class Interface(object):

    def __init__(self, adress):
        self.adress = adress
        self.history = {}


    def last_plugin_access(self, pluginName, account):
        if (pluginName, account) in self.history:
            return self.history[(pluginName, account)]
        return 0


    def use_for(self, pluginName, account):
        self.history[(pluginName, account)] = time.time()


    def __repr__(self):
        return "<Interface - %s>" % self.adress
