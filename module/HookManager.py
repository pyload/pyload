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

    @author: RaNaN, mkaay
"""
import __builtin__

from traceback import print_exc
from thread import start_new_thread
from threading import RLock

from types import MethodType

from module.threads.HookThread import HookThread
from module.plugins.PluginManager import literal_eval
from utils import lock

class HookManager:
    """ Manages hooks, loading, unloading.  """

    def __init__(self, core):
        self.core = core
        self.config = self.core.config

        __builtin__.hookManager = self #needed to let hooks register themself

        self.log = self.core.log
        self.plugins = {}
        self.methods = {} # dict of names and list of methods usable by rpc
        self.events = {} # Contains event that will be registred

        self.lock = RLock()
        self.createIndex()

        #registering callback for config event
        self.config.changeCB = MethodType(self.dispatchEvent, "configChanged", basestring)

        # manage hooks an config change
        self.addEvent("configChanged", self.manageHooks)

    @lock
    def callInHooks(self, event, *args):
        """  Calls a method in all hooks and catch / log errors"""
        for plugin in self.plugins.itervalues():
            self.call(plugin, event, *args)
        self.dispatchEvent(event, *args)

    def call(self, hook, f, *args):
        try:
            func = getattr(hook, f)
            return func(*args)
        except Exception, e:
            plugin.logError(_("Error executing %s" % event), e)
            if self.core.debug:
                print_exc()

    def addRPC(self, plugin, func, doc):
        plugin = plugin.rpartition(".")[2]
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

        for pluginname in self.core.pluginManager.getPlugins("hooks"):
            try:
                #hookClass = getattr(plugin, plugin.__name__)

                if self.core.config.get(pluginname, "activated"):
                    pluginClass = self.core.pluginManager.loadClass("hooks", pluginname)
                    if not pluginClass: continue

                    plugin = pluginClass(self.core, self)
                    self.plugins[pluginClass.__name__] = plugin
                    if plugin.isActivated():
                        active.append(pluginClass.__name__)
                else:
                    deactive.append(pluginname)


            except:
                self.log.warning(_("Failed activating %(name)s") % {"name": pluginname})
                if self.core.debug:
                    print_exc()

        self.log.info(_("Activated plugins: %s") % ", ".join(sorted(active)))
        self.log.info(_("Deactivate plugins: %s") % ", ".join(sorted(deactive)))

    def manageHooks(self, plugin, name, value):
        # check if section was a plugin
        if plugin not in self.core.pluginManager.getPlugins("hooks"):
            return

        if name == "activated" and value:
            self.activateHook(plugin)
        elif name == "activated" and not value:
            self.deactivateHook(plugin)

    @lock
    def activateHook(self, plugin):
        #check if already loaded
        if plugin in self.plugins:
            return

        pluginClass = self.core.pluginManager.loadClass("hooks", plugin)

        if not pluginClass: return

        self.log.debug("Plugin loaded: %s" % plugin)

        plugin = pluginClass(self.core, self)
        self.plugins[pluginClass.__name__] = plugin

        # active the hook in new thread
        start_new_thread(plugin.activate, tuple())

    @lock
    def deactivateHook(self, plugin):
        if plugin not in self.plugins:
            return
        else:
            hook = self.plugins[plugin]

        self.call(hook, "deactivate")
        self.log.debug("Plugin deactivated: %s" % plugin)

        #remove periodic call
        self.log.debug("Removed callback %s" % self.core.scheduler.removeJob(hook.cb))
        del self.plugins[hook.__name__]

        #remove event listener
        for f in dir(hook):
            if f.startswith("__") or type(getattr(hook, f)) != MethodType:
                continue
            self.core.eventManager.removeFromEvents(getattr(hook, f))

    def activateHooks(self):
        self.log.info(_("Activating Plugins..."))
        for plugin in self.plugins.itervalues():
            if plugin.isActivated():
                self.call(plugin, "activate")

    def deactivateHooks(self):
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
        HookThread(self.core.threadManager, function, args, kwargs)

    def activePlugins(self):
        """ returns all active plugins """
        return [x for x in self.plugins if x.isActivated()]

    def getAllInfo(self):
        """returns info stored by hook plugins"""
        info = {}
        for name, plugin in self.plugins.iteritems():
            if plugin.info:
                #copy and convert so str
                info[name] = dict(
                    [(x, str(y) if not isinstance(y, basestring) else y) for x, y in plugin.info.iteritems()])
        return info

    def getInfo(self, plugin):
        info = {}
        if plugin in self.plugins and self.plugins[plugin].info:
            info = dict([(x, str(y) if not isinstance(y, basestring) else y)
            for x, y in self.plugins[plugin].info.iteritems()])

        return info

    def addEvent(self, *args):
        self.core.eventManager.addEvent(*args)

    def dispatchEvent(self, *args):
        self.core.eventManager.dispatchEvent(*args)
    
