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
    @interface-version: 0.1
"""
import __builtin__

import traceback
from thread import start_new_thread
from threading import RLock
from time import time

from types import MethodType

from module.PluginThread import HookThread
from module.plugins.PluginManager import literal_eval
from utils import lock

class HookManager:
    """Manages hooks, delegates and handles Events.

        Every plugin can define events, \
        but some very usefull events are called by the Core.
        Contrary to overwriting hook methods you can use event listener,
        which provides additional entry point in the control flow.
        Only do very short tasks or use threads.

        **Known Events:**
        Most hook methods exists as events. These are the additional known events.

        ===================== ============== ==================================
        Name                     Arguments      Description
        ===================== ============== ==================================
        downloadPreparing     fid            A download was just queued and will be prepared now.
        downloadStarts        fid            A plugin will immediately starts the download afterwards.
        linksAdded            links, pid     Someone just added links, you are able to modify the links.
        allDownloadsProcessed                Every link was handled, pyload would idle afterwards.
        allDownloadsFinished                 Every download in queue is finished.
        unrarFinished         folder, fname  An Unrar job finished
        configChanged                        The config was changed via the api.
        pluginConfigChanged                  The plugin config changed, due to api or internal process.
        ===================== ============== ==================================

        | Notes:
        |    allDownloadsProcessed is *always* called before allDownloadsFinished.
        |    configChanged is *always* called before pluginConfigChanged.


    """

    def __init__(self, core):
        self.core = core
        self.config = self.core.config

        __builtin__.hookManager = self #needed to let hooks register themself

        self.log = self.core.log
        self.plugins = []
        self.pluginMap = {}
        self.methods = {} #dict of names and list of methods usable by rpc

        self.events = {} # contains events

        #registering callback for config event
        self.config.pluginCB = MethodType(self.dispatchEvent, "pluginConfigChanged", basestring)

        self.addEvent("pluginConfigChanged", self.activateHooks)

        self.lock = RLock()
        self.createIndex()

    def try_catch(func):
        def new(*args):
            try:
                return func(*args)
            except Exception, e:
                args[0].log.error(_("Error executing hooks: %s") % str(e))
                if args[0].core.debug:
                    traceback.print_exc()

        return new


    def addRPC(self, plugin, func, doc):
        plugin = plugin.rpartition(".")[2]
        doc = doc.strip() if doc else ""

        if plugin in self.methods:
            self.methods[plugin][func] = doc
        else:
            self.methods[plugin] = {func: doc}

    def callRPC(self, plugin, func, args, parse):
        if not args: args = tuple()
        if parse:
            args = tuple([literal_eval(x) for x in args])

        plugin = self.pluginMap[plugin]
        f = getattr(plugin, func)
        return f(*args)


    def createIndex(self):
        plugins = []

        active = []
        deactive = []

        for pluginname in self.core.pluginManager.hookPlugins:
            try:
                #hookClass = getattr(plugin, plugin.__name__)

                if self.core.config.getPlugin(pluginname, "activated"):
                    pluginClass = self.core.pluginManager.getHookPlugin(pluginname)
                    if not pluginClass: continue
                    
                    plugin = pluginClass(self.core, self)
                    plugins.append(plugin)
                    self.pluginMap[pluginClass.__name__] = plugin
                    if plugin.isActivated():
                        active.append(pluginClass.__name__)
                else:
                    deactive.append(pluginname)


            except:
                self.log.warning(_("Failed activating %(name)s") % {"name": pluginname})
                if self.core.debug:
                    traceback.print_exc()

        self.log.info(_("Activated plugins: %s") % ", ".join(sorted(active)))
        self.log.info(_("Deactivate plugins: %s") % ", ".join(sorted(deactive)))

        self.plugins = plugins

    def activateHooks(self, plugin, name, value):

        if name != "activated" or not value:
            return

        #check if already loaded
        for inst in self.plugins:
            if inst.__name__ == plugin:
                return


        pluginClass = self.core.pluginManager.getHookPlugin(plugin)

        if not pluginClass: return

        self.log.debug("Plugin loaded: %s" % plugin)

        plugin = pluginClass(self.core, self)
        self.plugins.append(plugin)
        self.pluginMap[pluginClass.__name__] = plugin

        # call core Ready
        start_new_thread(plugin.coreReady, tuple())

        # init periodical call
        self.core.scheduler.addJob(0, self.wrapPeriodical, args=[plugin], threaded=False)


    def wrapPeriodical(self, plugin):
        plugin.lastCall = time()
        try:
            if plugin.isActivated(): plugin.periodical()
        except Exception, e:
            self.core.log.error(_("Error executing hooks: %s") % str(e))
            if self.core.debug:
                traceback.print_exc()

        self.core.scheduler.addJob(plugin.interval, self.wrapPeriodical, args=[plugin], threaded=False)

    def initPeriodical(self):
        for plugin in self.plugins:
            if plugin.isActivated() and plugin.interval >= 1:
                self.core.scheduler.addJob(0, self.wrapPeriodical, args=[plugin], threaded=False)


    @try_catch
    def coreReady(self):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.coreReady()

        self.dispatchEvent("coreReady")
        self.initPeriodical()

    @lock
    def downloadStarts(self, pyfile):
        #TODO: rename to downloadPreparing
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.downloadStarts(pyfile)

        self.dispatchEvent("downloadPreparing", pyfile)

    @lock
    def downloadFinished(self, pyfile):
        for plugin in self.plugins:
            if plugin.isActivated():
                if "downloadFinished" in plugin.__threaded__:
                    self.startThread(plugin.downloadFinished, pyfile)
                else:
                    plugin.downloadFinished(pyfile)

        self.dispatchEvent("downloadFinished", pyfile)

    @lock
    def packageFinished(self, package):
        for plugin in self.plugins:
            if plugin.isActivated():
                if "packageFinished" in plugin.__threaded__:
                    self.startThread(plugin.packageFinished, package)
                else:
                    plugin.packageFinished(package)

        self.dispatchEvent("packageFinished", package)

    @lock
    def beforeReconnecting(self, ip):
        for plugin in self.plugins:
            plugin.beforeReconnecting(ip)

        self.dispatchEvent("beforeReconnecting", ip)

    @lock
    def afterReconnecting(self, ip):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.afterReconnecting(ip)

        self.dispatchEvent("afterReconnecting", ip)

    @lock
    def unrarFinished(self, folder, fname):
        self.dispatchEvent("unrarFinished", folder, fname)

    def startThread(self, function, pyfile):
        t = HookThread(self.core.threadManager, function, pyfile)

    def activePlugins(self):
        """ returns all active plugins """
        return [x for x in self.plugins if x.isActivated()]

    def getAllInfo(self):
        """returns info stored by hook plugins"""
        info = {}
        for name, plugin in self.pluginMap.iteritems():
            if plugin.info:
                #copy and convert so str
                info[name] = dict([(x, str(y) if type(y) != basestring else y) for x, y in plugin.info.iteritems()])
        return info


    def getInfo(self, plugin):
        info = {}
        if plugin in self.pluginMap and self.pluginMap[plugin].info:
            info = dict([(x, str(y) if type(y) != basestring else y)
                for x, y in self.pluginMap[plugin].info.iteritems()])

        return info

    def addEvent(self, event, func):
        """Adds an event listener for event name"""
        if event in self.events:
            self.events[event].append(func)
        else:
            self.events[event] = [func]

    def removeEvent(self, event, func):
        """removes previously added event listener"""
        if event in self.events:
            self.events[event].remove(func)

    def dispatchEvent(self, event, *args):
        """dispatches event with args"""
        if event in self.events:
            for f in self.events[event]:
                try:
                    f(*args)
                except Exception, e:
                    self.log.debug("Error calling event handler %s: %s, %s, %s"
                    % (event, f, args, str(e)))
    
