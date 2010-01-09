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

from os.path import basename, join
from glob import glob

from threading import Lock

from module.XMLConfigParser import XMLConfigParser


class HookManager():
    def __init__(self, core):
        self.core = core
        self.configParser = XMLConfigParser(join("module","config","plugin.xml"))
        self.configParser.loadData()
        self.config = self.configParser.getConfig()
        self.logger = logging.getLogger("log")
        self.plugins = []
        self.lock = Lock()
        self.createIndex()
    
    def createIndex(self):
        self.lock.acquire()
        pluginFiles = glob(join(self.core.plugin_folder, "hooks", "*.py"))
        plugins = []
        for pluginFile in pluginFiles:
            pluginName = basename(pluginFile).replace(".py", "")
            if pluginName == "Hook" or pluginName == "__init__":
                continue
            if pluginName in self.config.keys():
                if not self.config[pluginName]["activated"]:
                    continue
            else:
                self.configParser.set(pluginName, {"option": "activated", "type": "bool", "name": "Activated"}, True)
            module = __import__("module.plugins.hooks." + pluginName, globals(), locals(), [pluginName], -1)
            pluginClass = getattr(module, pluginName)
            pluginLoaded = pluginClass(self.core)
            pluginLoaded.setup()         
            plugins.append(pluginLoaded)
            
            self.logger.info("Installed Hook: %s" % pluginName)
        self.plugins = plugins
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
