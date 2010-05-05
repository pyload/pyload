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
import re
from threading import Lock

from module.XMLConfigParser import XMLConfigParser
from module.plugins.Hoster import Hoster

from sys import version_info

class PluginManager():
    def __init__(self, core):
        self.core = core
        self.configParser = self.core.xmlconfig
        self.configParser.loadData()
        self.config = self.configParser.getConfig()
        self.logger = logging.getLogger("log")
        self.crypterPlugins = []
        self.containerPlugins = []
        self.hosterPlugins = []
        self.captchaPlugins = []
        self.accountPlugins = []
        self.lock = Lock()
        self.createIndex()
    
    def createIndex(self):
        self.lock.acquire()
        
        self.crypterPlugins = self.parse(self.core.config["plugins"]["load_crypter_plugins"], _("Crypter"))
        self.containerPlugins = self.parse(self.core.config["plugins"]["load_container_plugins"], _("Container"))
        self.hosterPlugins = self.parse(self.core.config["plugins"]["load_hoster_plugins"], _("Hoster"))
        self.captchaPlugins = self.parse(self.core.config["plugins"]["load_captcha_plugins"], _("Captcha"))
        #self.accountPlugins = self.parse(self.core.config["plugins"]["load_account_plugins"], _("Account"))
        
        self.lock.release()
        self.logger.info(_("created index of plugins"))
    
    def parse(self, pluginStr, ptype):
        plugins = []
        for pluginModule in pluginStr.split(","):
            pluginModule = pluginModule.strip()
            if not pluginModule:
                continue
            pluginName = pluginModule.split(".")[-1]
            if pluginName.endswith("_25") and not version_info == (2, 5):
                continue
            elif pluginName.endswith("_26") and not version_info == (2, 6):
                continue
            module = __import__(pluginModule, globals(), locals(), [pluginName], -1)
            pluginClass = getattr(module, pluginName)
            try:
                plugins.append(pluginClass)
                self.logger.debug(_("%(type)s: %(name)s added") % {"name":pluginName, "type":ptype})
            except:
                pass
        return plugins
    
    def getPluginFromPattern(self, urlPattern):
        plugins = []
        plugins.extend(self.crypterPlugins)
        plugins.extend(self.containerPlugins)
        plugins.extend(self.hosterPlugins)
        for plugin in plugins:
            if not plugin.__pattern__:
                continue
            if re.match(plugin.__pattern__, urlPattern):
                return plugin
        return Hoster
    
    def getCaptchaPlugin(self, name):
        for plugin in self.captchaPlugins:
            if plugin.__name__ == name:
                return plugin
        return None
    
    def getAccountPlugin(self, name): # not implemeted yet!
        for plugin in self.accountPlugins:
            if plugin.__name__ == name:
                return plugin
        return None
