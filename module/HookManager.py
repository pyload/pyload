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
    @interface-version: 0.1
"""

import traceback
from threading import RLock
from module.PluginThread import HookThread
from time import time

class HookManager():
    def __init__(self, core):
        self.core = core

        self.config = self.core.config

        self.log = self.core.log
        self.plugins = []
        self.lock = RLock()
        self.createIndex()

    def lock(func):
        def new(*args):
            args[0].lock.acquire()
            res = func(*args)
            args[0].lock.release()
            return res
        return new
    
    def try_catch(func):
        def new(*args):
            try:
                return func(*args)
            except Exception, e:
                args[0].log.error(_("Error executing hooks: %s") % str(e))
        return new

    def createIndex(self):

        plugins = []
        for pluginClass in self.core.pluginManager.getHookPlugins():
            try:
                #hookClass = getattr(plugin, plugin.__name__)
                
                if self.core.config.getPlugin(pluginClass.__name__, "load"):
                    #@TODO handle in pluginmanager
                    plugin = pluginClass(self.core)
                    plugins.append(plugin)
                    self.log.info(_("%s loaded, activated %s") % (pluginClass.__name__, plugin.isActivated() ))
            except:
                self.log.warning(_("Failed activating %(name)s") % {"name":pluginClass.__name__})
                if self.core.debug:
                    traceback.print_exc()

        self.plugins = plugins


    def periodical(self):
        for plugin in self.plugins:
            if plugin.isActivated() and plugin.lastCall + plugin.interval < time():
                plugin.periodical()
                plugin.lastCall = time()
    
    
    @try_catch
    def coreReady(self):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.coreReady()

    @lock
    def downloadStarts(self, pyfile):

        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.downloadStarts(pyfile)

    @lock
    def downloadFinished(self, pyfile):

        for plugin in self.plugins:
            if plugin.isActivated():
                if "downloadFinished" in plugin.__threaded__:
                    self.startThread(plugin.downloadFinished, pyfile)
                else:
                    plugin.downloadFinished(pyfile)
    
    @lock
    def packageFinished(self, package):

        for plugin in self.plugins:
            if plugin.isActivated():
                if "packageFinished" in plugin.__threaded__:
                    self.startThread(plugin.packageFinished, package)
                else:
                    plugin.packageFinished(package)
    
    @lock
    def beforeReconnecting(self, ip):

        for plugin in self.plugins:
            plugin.beforeReconnecting(ip)
    
    @lock
    def afterReconnecting(self, ip):

        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.afterReconnecting(ip)

    def startThread(self, function, pyfile):
        t = HookThread(self.core.threadManager, function, pyfile)
