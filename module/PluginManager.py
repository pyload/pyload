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
    
    @author: mkaay, RaNaN
"""

import re
import sys

from os import listdir
from os import makedirs

from os.path import isfile
from os.path import join
from os.path import exists
from os.path import abspath

from sys import version_info
from itertools import chain


class PluginManager():
    def __init__(self, core):
        self.core = core
        
        #self.config = self.core.config
        self.log = core.log
        
        self.crypterPlugins = {}
        self.containerPlugins = {}
        self.hosterPlugins = {}
        self.captchaPlugins = {}
        self.accountPlugins = {}
        self.hookPlugins = {}
        
        self.createHomeDirs()
        
        self.createIndex()
        
        #@TODO plugin updater
    #----------------------------------------------------------------------
    def createHomeDirs(self):
        """create homedirectories containing plugins"""
        #@TODO implement...
        pass
    
    def createIndex(self):
        """create information for all plugins available"""
        
        sys.path.append(abspath(""))
        
        if not exists("userplugins"):
            makedirs("userplugins")
        if not exists(join("userplugins", "__init__.py")):
            f = open(join("userplugins", "__init__.py"), "wb")
            f.close()
        
        self.rePattern = re.compile(r'__pattern__.*=.*r("|\')([^"\']+)')
        self.reVersion = re.compile(r'__version__.*=.*("|\')([0-9.]+)')
        self.reConfig = re.compile(r'__config__.*=.*\[([^\]]+)', re.MULTILINE)
        
        self.crypterPlugins = self.parse(_("Crypter"), "crypter", pattern=True)
        self.containerPlugins = self.parse(_("Container"), "container", pattern=True)
        self.hosterPlugins = self.parse(_("Hoster") ,"hoster", pattern=True)
        
        self.captchaPlugins = self.parse(_("Captcha"), "captcha")
        self.accountPlugins = self.parse(_("Account"), "accounts", create=True)
        self.hookPlugins = self.parse(_("Hook"), "hooks")
        
        self.log.info(_("created index of plugins"))
    
    def parse(self, typ, folder, create=False, pattern=False, home={}):
        """
        returns dict with information 
        home contains parsed plugins from module.
        
        {
        name : {path, version, config, (pattern, re), (plugin, class)}
        }
        
        """
        plugins = {}
        if home:
            pfolder = join("userplugins", folder)
            if not exists(pfolder):
                makedirs(pfolder)
            if not exists(join(pfolder, "__init__.py")):
                f = open(join(pfolder, "__init__.py"), "wb")
                f.close()

        else:
            pfolder = join(pypath, "module", "plugins", folder)
            
        for f in listdir(pfolder):
            if (isfile(join(pfolder, f)) and f.endswith(".py") or f.endswith("_25.pyc") or f.endswith("_26.pyc") or f.endswith("_27.pyc")) and not f.startswith("_"):
                data = open(join(pfolder, f))
                content = data.read()
                data.close()
                
                if f.endswith("_25.pyc") and not version_info[0:2] == (2, 5):
                    continue
                elif f.endswith("_26.pyc") and not version_info[0:2] == (2, 6):
                    continue
                elif f.endswith("_27.pyc") and not version_info[0:2] == (2, 7):
                    continue
                                              
                name = f[:-3]
                if name[-1] == "." : name = name[:-4]
                
                
                version = self.reVersion.findall(content)
                if version:
                    version = float(version[0][1])
                else:
                    version = 0
                
                if home and home.has_key(name):
                    if home[name]["v"] > version:
                        continue
                
                
                plugins[name] = {}
                plugins[name]["v"] = version
                
                
                module = f.replace(".pyc","").replace(".py","")
                if home:
                    path = "userplugins.%s.%s" % (folder, module)
                else:
                    path = "module.plugins.%s.%s" % (folder, module)
                    
                plugins[name]["name"] = module                
                plugins[name]["path"] = path
                
                
                if pattern:
                    pattern = self.rePattern.findall(content)
                    
                    if pattern:
                        pattern = pattern[0][1]
                    else:
                        pattern = "^unmachtable$"
                        
                    plugins[name]["pattern"] = pattern
                    
                    try:
                        plugins[name]["re"] = re.compile(pattern)
                    except:
                        self.log.error(_("%s has invalid pattern.") % name)

                
                config = self.reConfig.findall(content)
                
                if config:
                    config = [ [y.strip() for y in x.replace("'","").replace('"',"").replace(")","").split(",")] for x in config[0].split("(") if x.strip()]
                    
                    if folder == "hooks":
                        config.append( ["load", "bool", "Load on startup", True if name not in ("XMPPInterface", "MultiHome") else False] ) 
                    
                    for item in config:
                        self.core.config.addPluginConfig([name]+item)
    
        if not home:
            temp = self.parse(typ, folder, create, pattern, plugins)
            plugins.update(temp)
            
        return plugins
        
    #----------------------------------------------------------------------
    def parseUrls(self, urls):
        """parse plugins for given list of urls"""
        
        last = None
        res = [] # tupels of (url, plugin)
        
        for url in urls:

            found = False
            
            if last and last[1]["re"].match(url):
                res.append((url, last[0]))
                continue
            
            for name, value in chain(self.crypterPlugins.iteritems(), self.hosterPlugins.iteritems(), self.containerPlugins.iteritems() ):
                if value["re"].match(url):
                    res.append((url, name))
                    last = (name, value)
                    found = True
                    break
                
            if not found:
                res.append((url, "BasePlugin")) 
        
        return res
    
    #----------------------------------------------------------------------
    def getPlugin(self, name):
        """return plugin module from hoster|decrypter|container"""
        plugin = None
        
        if self.containerPlugins.has_key(name):
            plugin = self.containerPlugins[name]
        if self.crypterPlugins.has_key(name):
            plugin = self.crypterPlugins[name]
        if self.hosterPlugins.has_key(name):
            plugin = self.hosterPlugins[name]
        
            
        if plugin.has_key("module"):
            return plugin["module"]
        
        plugin["module"] = __import__(plugin["path"], globals(), locals(), [plugin["name"]] , -1)
        
        return plugin["module"]
        
            
    #----------------------------------------------------------------------
    def getCaptchaPlugin(self, name):
        """return captcha modul if existent"""
        if self.captchaPlugins.has_key(name):
            plugin = self.captchaPlugins[name]
            if plugin.has_key("class"):
                return plugin["class"]
        
            module = __import__(plugin["path"], globals(), locals(), [plugin["name"]] , -1)
            plugin["class"] = getattr(module, name)
        
            return plugin["class"]
        
        return None
    #----------------------------------------------------------------------
    def getAccountPlugin(self, name):
        """return account class if existent"""
        if self.accountPlugins.has_key(name):
            plugin = self.accountPlugins[name]
            if plugin.has_key("class"):
                return plugin["class"]
            
            module = __import__(plugin["path"], globals(), locals(), [plugin["name"]] , -1)
            plugin["class"] = getattr(module, plugin["name"])
                 
            return plugin["class"]
        
        return None
        
    #----------------------------------------------------------------------
    def getAccountPlugins(self):
        """return list of account plugin names"""
        res = []
        
        for name in self.accountPlugins.keys():
            res.append(name)
    
        return res
    #----------------------------------------------------------------------
    def getHookPlugins(self):
        """return list of hook classes"""
        
        classes = []
        
        for name, value in self.hookPlugins.iteritems():
            if value.has_key("class"):
                classes.append(value["class"])
                continue
            
            if not self.core.config.getPlugin(name, "load"):
                continue
            
            try:
                module = __import__(value["path"], globals(), locals(), [value["name"]] , -1)
            except Exception, e:
                self.log.error(_("Error importing %(name): %(msg)") % {"name": name, "msg": str(e) })
                self.log.error(_("You should fix dependicies or deactivate load on startup."))
                continue
                
            pluginClass = getattr(module, name)
            
            value["class"] = pluginClass

            classes.append(pluginClass)            
        
        return classes


if __name__ == "__main__":
    _ = lambda x : x
    pypath = "/home/christian/Projekte/pyload-0.4/module/plugins"
    
    from time import time
    
    p = PluginManager(None)
    
    a = time() 
    
    test = [ "http://www.youtube.com/watch?v=%s" % x for x in range(0,100) ]
    print p.parseUrls(test)
    
    b = time()
    
    print b-a ,"s"
    
