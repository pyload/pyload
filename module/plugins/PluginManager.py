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

from os import listdir, makedirs
from os.path import isfile, join, exists, abspath
from sys import version_info
from itertools import chain
from traceback import print_exc

try:
    from ast import literal_eval
except ImportError: # python 2.5
    from module.lib.SafeEval import safe_eval as literal_eval

from module.ConfigParser import IGNORE

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

        self.plugins = {"crypter": self.crypterPlugins,
                        "container": self.containerPlugins,
                        "hoster": self.hosterPlugins,
                        "captcha": self.captchaPlugins,
                        "accounts": self.accountPlugins,
                        "hooks": self.hookPlugins}

        self.createIndex()


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
        self.reDesc = re.compile(r'__description__.?=.?("|"""|\')([^"\']+)')

        self.crypterPlugins = self.parse(_("Crypter"), "crypter", pattern=True)
        self.containerPlugins = self.parse(_("Container"), "container", pattern=True)
        self.hosterPlugins = self.parse(_("Hoster"), "hoster", pattern=True)

        self.captchaPlugins = self.parse(_("Captcha"), "captcha")
        self.accountPlugins = self.parse(_("Account"), "accounts", create=True)
        self.hookPlugins = self.parse(_("Hook"), "hooks")

        self.log.debug("created index of plugins")

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
            if (isfile(join(pfolder, f)) and f.endswith(".py") or f.endswith("_25.pyc") or f.endswith(
                "_26.pyc") or f.endswith("_27.pyc")) and not f.startswith("_"):
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
                if name[-1] == ".": name = name[:-4]

                version = self.reVersion.findall(content)
                if version:
                    version = float(version[0][1])
                else:
                    version = 0

                if home and name in home:
                    if home[name]["v"] >= version:
                        continue

                plugins[name] = {}
                plugins[name]["v"] = version

                module = f.replace(".pyc", "").replace(".py", "")
                if home:
                    if name in IGNORE:
                        del plugins[name]
                        continue
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
                        self.log.error(_("%s has a invalid pattern.") % name)

                config = self.reConfig.findall(content)

                if config:
                    config = literal_eval(config[0].strip().replace("\n", "").replace("\r", ""))
                    desc = self.reDesc.findall(content)
                    if desc:
                        desc = desc[0][1]
                    else:
                        desc = ""

                    if type(config[0]) == tuple:
                        config = [list(x) for x in config]
                    else:
                        config = [list(config)]



                    if folder == "hooks":
                        append = True
                        for item in config:
                            if item[0] == "activated": append = False

                        # activated flag missing
                        if append: config.append(["activated", "bool", "Activated", False])

                    try:
                        self.core.config.addPluginConfig(name, config, desc)
                    except :
                        self.log.error("Invalid config in %s: %s" % (name, config))

        if not home:
            temp = self.parse(typ, folder, create, pattern, plugins)
            plugins.update(temp)

        return plugins


    def parseUrls(self, urls):
        """parse plugins for given list of urls"""

        last = None
        res = [] # tupels of (url, plugin)

        for url in urls:
            if type(url) not in (str, unicode, buffer): continue
            found = False

            if last and last[1]["re"].match(url):
                res.append((url, last[0]))
                continue

            for name, value in chain(self.crypterPlugins.iteritems(), self.hosterPlugins.iteritems(),
                                     self.containerPlugins.iteritems()):
                if value["re"].match(url):
                    res.append((url, name))
                    last = (name, value)
                    found = True
                    break

            if not found:
                res.append((url, "BasePlugin"))

        return res


    def getPlugin(self, name, original=False):
        """return plugin module from hoster|decrypter|container"""
        plugin = None

        if name in self.containerPlugins:
            plugin = self.containerPlugins[name]
        if name in self.crypterPlugins:
            plugin = self.crypterPlugins[name]
        if name in self.hosterPlugins:
            plugin = self.hosterPlugins[name]

        if not plugin:
            self.log.warning("Plugin %s not found." % name)
            plugin = self.hosterPlugins["BasePlugin"]

        if "new_module" in plugin and not original:
            return plugin["new_module"]

        if "module" in plugin:
            return plugin["module"]

        plugin["module"] = __import__(plugin["path"], globals(), locals(), [plugin["name"]], -1)

        return plugin["module"]

    def getPluginName(self, name):
        """ used to obtain new name if other plugin was injected"""
        plugin = None
        if name in self.containerPlugins:
            plugin = self.containerPlugins[name]
        if name in self.crypterPlugins:
            plugin = self.crypterPlugins[name]
        if name in self.hosterPlugins:
            plugin = self.hosterPlugins[name]

        if "new_name" in plugin:
            return plugin["new_name"]
        
        return name



    def getCaptchaPlugin(self, name):
        """return captcha modul if existent"""
        if name in self.captchaPlugins:
            plugin = self.captchaPlugins[name]
            if "class" in plugin:
                return plugin["class"]

            module = __import__(plugin["path"], globals(), locals(), [plugin["name"]], -1)
            plugin["class"] = getattr(module, name)

            return plugin["class"]

        return None


    def getAccountPlugin(self, name):
        """return account class if existent"""
        if name in self.accountPlugins:
            plugin = self.accountPlugins[name]
            if "class" in plugin:
                return plugin["class"]

            module = __import__(plugin["path"], globals(), locals(), [plugin["name"]], -1)
            plugin["class"] = getattr(module, plugin["name"])

            return plugin["class"]

        return None


    def getAccountPlugins(self):
        """return list of account plugin names"""
        res = []

        for name in self.accountPlugins.keys():
            res.append(name)

        return res

    def getHookPlugin(self, name):

        if name not in self.hookPlugins: return None

        value = self.hookPlugins[name]

        if "class" in value:
            return value["class"]

        try:
            module = __import__(value["path"], globals(), locals(), [value["name"]], -1)
            pluginClass = getattr(module, name)
        except Exception, e:
            self.log.error(_("Error importing %(name)s: %(msg)s") % {"name": name, "msg": str(e)})
            self.log.error(_("You should fix dependicies or deactivate it."))
            if self.core.debug:
                print_exc()
            return None

        value["class"] = pluginClass

        return pluginClass

    
    def reloadPlugins(self):
        """ reloads and reindexes plugins """
        pass


if __name__ == "__main__":
    _ = lambda x: x
    pypath = "/home/christian/Projekte/pyload-0.4/module/plugins"

    from time import time

    p = PluginManager(None)

    a = time()

    test = ["http://www.youtube.com/watch?v=%s" % x for x in range(0, 100)]
    print p.parseUrls(test)

    b = time()

    print b - a, "s"
    
