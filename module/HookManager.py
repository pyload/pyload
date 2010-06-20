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

import logging
import traceback
from threading import Lock

from module.XMLConfigParser import XMLConfigParser

class HookManager():
    def __init__(self, core):
        self.core = core
        self.configParser = self.core.parser_plugins
        self.configParser.loadData()
        self.config = self.configParser.getConfig()
        self.logger = logging.getLogger("log")
        self.plugins = []
        self.lock = Lock()
        self.createIndex()
    
    def createIndex(self):
        self.lock.acquire()

        plugins = []
        for pluginClass in self.core.pluginManager.getHookPlugins():
            try:
                plugin = pluginClass(self.core)
                plugin.readConfig()
                plugins.append(plugin)
            except:
                self.logger.warning(_("Failed activating %(name)s") % {"name":plugin.__name__})
                if self.core.config['general']['debug_mode']:
                    traceback.print_exc()
            
        self.plugins = plugins
        self.lock.release()
    
    def coreReady(self):
        self.lock.acquire()

        for plugin in self.plugins:
            plugin.coreReady()
        self.lock.release()
    
    def downloadStarts(self, pyfile):
        self.lock.acquire()

        for plugin in self.plugins:
            plugin.downloadStarts(pyfile)
        self.lock.release()
    
    def downloadFinished(self, pyfile):
        self.lock.acquire()

        for plugin in self.plugins:
            plugin.downloadFinished(pyfile)
        self.lock.release()

    def packageFinished(self, package):
        self.lock.acquire()

        for plugin in self.plugins:
            plugin.packageFinished(package)
        self.lock.release()

    def beforeReconnecting(self, ip):
        self.lock.acquire()

        for plugin in self.plugins:
            plugin.beforeReconnecting(ip)
        self.lock.release()
    
    def afterReconnecting(self, ip):
        self.lock.acquire()

        for plugin in self.plugins:
            plugin.afterReconnecting(ip)
        self.lock.release()
