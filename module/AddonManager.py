# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2013 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

import __builtin__

from thread import start_new_thread
from threading import RLock

from types import MethodType

from module.threads.AddonThread import AddonThread
from module.PluginManager import literal_eval
from utils import lock, to_string

class AddonManager:
    """ Manages addons, loading, unloading.  """

    def __init__(self, core):
        self.core = core
        self.config = self.core.config

        __builtin__.addonManager = self #needed to let addons register themselves

        self.log = self.core.log
        self.plugins = {}
        self.methods = {} # dict of names and list of methods usable by rpc
        self.events = {} # Contains event that will be registered

        self.lock = RLock()
        self.createIndex()

        # manage addons on config change
        self.addEvent("configChanged", self.manageAddons)

    @lock
    def callInHooks(self, event, *args):
        """  Calls a method in all addons and catch / log errors"""
        for plugin in self.plugins.itervalues():
            self.call(plugin, event, *args)
        self.dispatchEvent(event, *args)

    def call(self, addon, f, *args):
        try:
            func = getattr(addon, f)
            return func(*args)
        except Exception, e:
            addon.logError(_("Error when executing %s" % f), e)
            self.core.print_exc()

    def addRPC(self, plugin, func, doc):
        doc = doc.strip() if doc else ""

        if plugin in self.methods:
            self.methods[plugin][func] = doc
        else:
            self.methods[plugin] = {func: doc}

    def callRPC(self, plugin, func, args):
        if not args: args = []
        else:
            args = literal_eval(args)

        plugin = self.plugins[plugin]
        f = getattr(plugin, func)
        return f(*args)

    @lock
    def createIndex(self):
        active = []
        deactive = []

        for pluginname in self.core.pluginManager.getPlugins("addons"):
            try:
                # check first for builtin plugin
                attrs = self.core.pluginManager.loadAttributes("addons", pluginname)
                internal = attrs.get("internal", False)

                if internal or self.core.config.get(pluginname, "activated"):
                    pluginClass = self.core.pluginManager.loadClass("addons", pluginname)

                    if not pluginClass: continue

                    plugin = pluginClass(self.core, self)
                    self.plugins[pluginClass.__name__] = plugin

                    # hide internals from printing
                    if not internal and plugin.isActivated():
                        active.append(pluginClass.__name__)
                    else:
                        self.log.debug("Loaded internal plugin: %s" % pluginClass.__name__)
                else:
                    deactive.append(pluginname)


            except:
                self.log.warning(_("Failed activating %(name)s") % {"name": pluginname})
                self.core.print_exc()

        self.log.info(_("Activated addons: %s") % ", ".join(sorted(active)))
        self.log.info(_("Deactivate addons: %s") % ", ".join(sorted(deactive)))

    def manageAddons(self, plugin, name, value):
        # check if section was a plugin
        if plugin not in self.core.pluginManager.getPlugins("addons"):
            return

        if name == "activated" and value:
            self.activateAddon(plugin)
        elif name == "activated" and not value:
            self.deactivateAddon(plugin)

    @lock
    def activateAddon(self, plugin):
        #check if already loaded
        if plugin in self.plugins:
            return

        pluginClass = self.core.pluginManager.loadClass("addons", plugin)

        if not pluginClass: return

        self.log.debug("Plugin loaded: %s" % plugin)

        plugin = pluginClass(self.core, self)
        self.plugins[pluginClass.__name__] = plugin

        # active the addon in new thread
        start_new_thread(plugin.activate, tuple())
        self.registerEvents() # TODO: BUG: events will be destroyed and not re-registered

    @lock
    def deactivateAddon(self, plugin):
        if plugin not in self.plugins:
            return
        else:
            addon = self.plugins[plugin]

        if addon.__internal__: return

        self.call(addon, "deactivate")
        self.log.debug("Plugin deactivated: %s" % plugin)

        #remove periodic call
        self.log.debug("Removed callback %s" % self.core.scheduler.removeJob(addon.cb))
        del self.plugins[addon.__name__]

        #remove event listener
        for f in dir(addon):
            if f.startswith("__") or type(getattr(addon, f)) != MethodType:
                continue
            self.core.eventManager.removeFromEvents(getattr(addon, f))

    def activateAddons(self):
        self.log.info(_("Activating Plugins..."))
        for plugin in self.plugins.itervalues():
            if plugin.isActivated():
                self.call(plugin, "activate")

        self.registerEvents()

    def deactivateAddons(self):
        """  Called when core is shutting down """
        self.log.info(_("Deactivating Plugins..."))
        for plugin in self.plugins.itervalues():
            self.call(plugin, "deactivate")

    def downloadPreparing(self, pyfile):
        self.callInHooks("downloadPreparing", pyfile)

    def downloadFinished(self, pyfile):
        self.callInHooks("downloadFinished", pyfile)

    def downloadFailed(self, pyfile):
        self.callInHooks("downloadFailed", pyfile)

    def packageFinished(self, package):
        self.callInHooks("packageFinished", package)

    def beforeReconnecting(self, ip):
        self.callInHooks("beforeReconnecting", ip)

    def afterReconnecting(self, ip):
        self.callInHooks("afterReconnecting", ip)

    @lock
    def startThread(self, function, *args, **kwargs):
        AddonThread(self.core.threadManager, function, args, kwargs)

    def activePlugins(self):
        """ returns all active plugins """
        return [x for x in self.plugins.itervalues() if x.isActivated()]

    def getAllInfo(self):
        """returns info stored by addon plugins"""
        info = {}
        for name, plugin in self.plugins.iteritems():
            if plugin.info:
                #copy and convert so str
                info[name] = dict(
                    [(x, to_string(y)) for x, y in plugin.info.iteritems()])
        return info

    def getInfo(self, plugin):
        info = {}
        if plugin in self.plugins and self.plugins[plugin].info:
            info = dict([(x, to_string(y))
            for x, y in self.plugins[plugin].info.iteritems()])

        return info

    def addEventListener(self, plugin, func, event):
        """ add the event to the list """
        if plugin not in self.events:
            self.events[plugin] = []
        self.events[plugin].append((func, event))

    def registerEvents(self):
        """ actually register all saved events """
        for name, plugin in self.plugins.iteritems():
            if name in self.events:
                for func, event in self.events[name]:
                    self.addEvent(event, getattr(plugin, func))
                # clean up
                del self.events[name]

    def addConfigHandler(self, plugin, func):
        pass #TODO

    def addEvent(self, *args):
        self.core.eventManager.addEvent(*args)

    def dispatchEvent(self, *args):
        self.core.eventManager.dispatchEvent(*args)
    
