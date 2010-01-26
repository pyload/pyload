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
from glob import glob
import logging
from os import listdir
from os.path import basename
from os.path import join
import subprocess
from threading import Lock

from module.XMLConfigParser import XMLConfigParser

class HookManager():
    def __init__(self, core):
        self.core = core
        self.configParser = XMLConfigParser(join("module", "config", "plugin.xml"))
        self.configParser.loadData()
        self.config = self.configParser.getConfig()        
        self.logger = logging.getLogger("log")
        self.plugins = []
        self.scripts = {}
        self.lock = Lock()
        self.createIndex()
    
    def createIndex(self):
        self.lock.acquire()

        f = lambda x: False if x.startswith("#") or x.endswith("~") else True
        self.scripts = {}

        folder = join(self.core.path, "scripts")

        self.scripts['download_preparing'] = filter(f, listdir(join(folder, 'download_preparing')))
        self.scripts['download_finished'] = filter(f, listdir(join(folder, 'download_finished')))
        self.scripts['package_finished'] = filter(f, listdir(join(folder, 'package_finished')))
        self.scripts['before_reconnect'] = filter(f, listdir(join(folder, 'before_reconnect')))
        self.scripts['after_reconnect'] = filter(f, listdir(join(folder, 'after_reconnect')))

        for script_type, script_name in self.scripts.iteritems():
            if script_name != []:
                self.logger.info("Installed %s Scripts: %s" % (script_type, ", ".join(script_name)))

        #~ self.core.logger.info("Installed Scripts: %s" % str(self.scripts))

        self.folder = folder

        pluginFiles = glob(join(self.core.plugin_folder, "hooks", "*.py"))
        plugins = []
        for pluginFile in pluginFiles:
            pluginName = basename(pluginFile).replace(".py", "")
            if pluginName == "__init__":
                continue
            if pluginName in self.config.keys():
                if not self.config[pluginName]["activated"]:
                    self.logger.info("Deactivated %s" % pluginName)
                    continue
            else:
                self.configParser.set(pluginName, {"option": "activated", "type": "bool", "name": "Activated"}, True)
            module = __import__("module.plugins.hooks." + pluginName, globals(), locals(), [pluginName], -1)
            pluginClass = getattr(module, pluginName)
            plugin = pluginClass(self.core)
            plugin.readConfig()
            plugins.append(plugin)
            self.logger.info("Activated %s" % pluginName)
            
        self.plugins = plugins
        self.lock.release()
    
    def downloadStarts(self, pyfile):
        self.lock.acquire()

    	for script in self.scripts['download_preparing']:
            try:
                out = subprocess.Popen([join(self.folder, 'download_preparing', script), pyfile.plugin.props['name'], pyfile.url], stdout=subprocess.PIPE)
                out.wait()
            except:
                pass

        for plugin in self.plugins:
            plugin.downloadStarts(pyfile)
        self.lock.release()
    
    def downloadFinished(self, pyfile):
        self.lock.acquire()

        for script in self.scripts['download_finished']:
            try:
                out = subprocess.Popen([join(self.folder, 'download_finished', script), pyfile.plugin.props['name'], pyfile.url, pyfile.status.name, \
                join(self.core.path,self.core.config['general']['download_folder'], pyfile.folder, pyfile.status.name)], stdout=subprocess.PIPE)
            except:
                pass

        
        for plugin in self.plugins:
            plugin.downloadFinished(pyfile)
        self.lock.release()

    def packageFinished(self, pyfile, package):
        raise NotImplementedError

    def beforeReconnecting(self, ip):
        self.lock.acquire()

        for script in self.scripts['before_reconnect']:
            try:
                out = subprocess.Popen([join(self.folder, 'before_reconnect', script), ip], stdout=subprocess.PIPE)
                out.wait()
            except:
                pass

        for plugin in self.plugins:
            plugin.beforeReconnecting(ip)
        self.lock.release()
    
    def afterReconnecting(self, ip):
        self.lock.acquire()

        for script in self.scripts['after_reconnect']:
            try:
                out = subprocess.Popen([join(self.folder, 'download_preparing', script), ip], stdout=subprocess.PIPE)
            except:
                pass
        
        for plugin in self.plugins:
            plugin.afterReconnecting(ip)
        self.lock.release()
