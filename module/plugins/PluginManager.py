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

from module.lib.SafeEval import const_eval as literal_eval
from module.ConfigParser import IGNORE

class PluginManager:
    ROOT = "module.plugins."
    USERROOT = "userplugins."
    TYPES = ("crypter", "container", "hoster", "captcha", "accounts", "hooks", "internal")

    PATTERN = re.compile(r'__pattern__.*=.*r("|\')([^"\']+)')
    VERSION = re.compile(r'__version__.*=.*("|\')([0-9.]+)')
    CONFIG = re.compile(r'__config__.*=.*(\[[^\]]+\])', re.MULTILINE)
    DESC = re.compile(r'__description__.?=.?("|"""|\')([^"\']+)')


    def __init__(self, core):
        self.core = core

        #self.config = self.core.config
        self.log = core.log

        self.plugins = {}
        self.createIndex()

        #register for import hook
        sys.meta_path.append(self)


    def createIndex(self):
        """create information for all plugins available"""

        def merge(dst, src, overwrite=False):
            """merge dict of dicts"""
            for name in src:
                if name in dst:
                    if overwrite is True:
                        dst[name].update(src[name])
                    else:
                        for _k in set(src[name].keys()) - set(dst[name].keys()):
                            dst[name][_k] = src[name][_k]
                else:
                    dst[name] = src[name]

        sys.path.append(abspath(""))

        if not exists("userplugins"):
            makedirs("userplugins")
        if not exists(join("userplugins", "__init__.py")):
            f = open(join("userplugins", "__init__.py"), "wb")
            f.close()

        self.crypterPlugins , config = self.parse("crypter", pattern=True)
        self.plugins["crypter"] = self.crypterPlugins
        default_config = config

        self.containerPlugins, config = self.parse("container", pattern=True)
        self.plugins["container"] = self.containerPlugins
        merge(default_config, config)

        self.hosterPlugins, config = self.parse("hoster", pattern=True)
        self.plugins["hoster"] = self.hosterPlugins
        merge(default_config, config)

        self.hookPlugins, config = self.parse("hooks")
        self.plugins["hooks"] = self.hookPlugins
        merge(default_config, config)

        self.captchaPlugins, config = self.parse("captcha")
        self.plugins["captcha"] = self.captchaPlugins
        merge(default_config, config)

        self.accountPlugins, config = self.parse("accounts")
        self.plugins["accounts"] = self.accountPlugins
        merge(default_config, config)

        self.internalPlugins, config = self.parse("internal")
        self.plugins["internal"] = self.internalPlugins
        merge(default_config, config)

        for name, config in default_config.items():
            desc = config.pop('desc', "")
            config = [[k] + list(v) for k, v in config.items()]
            try:
                self.core.config.addPluginConfig(name, config, desc)
            except:
                self.log.error("Invalid config in %s: %s" % (name, config))

        self.log.debug("created index of plugins")

    def parse(self, folder, pattern=False, home={}):
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

        configs = {}
        for f in listdir(pfolder):
            if (isfile(join(pfolder, f)) and f.endswith(".py") or f.endswith("_25.pyc") or
                    f.endswith("_26.pyc") or f.endswith("_27.pyc")) and not f.startswith("_"):

                data = open(join(pfolder, f))
                content = data.read()
                data.close()

                if f.endswith("_25.pyc") and version_info[0:2] != (2, 5):
                    continue
                elif f.endswith("_26.pyc") and version_info[0:2] != (2, 6):
                    continue
                elif f.endswith("_27.pyc") and version_info[0:2] != (2, 7):
                    continue

                name = f[:-3]
                if name[-1] == ".": name = name[:-4]

                version = self.VERSION.findall(content)
                if version:
                    version = float(version[0][1])
                else:
                    version = 0

                # home contains plugins from pyload root
                if isinstance(home, dict) and name in home:
                    if home[name]["v"] >= version:
                        continue

                if name in IGNORE or (folder, name) in IGNORE:
                     continue

                plugins[name] = {}
                plugins[name]["v"] = version

                module = f.replace(".pyc", "").replace(".py", "")

                # the plugin is loaded from user directory
                plugins[name]["user"] = True if home else False
                plugins[name]["name"] = module

                if pattern:
                    pattern = self.PATTERN.findall(content)

                    if pattern:
                        pattern = pattern[0][1]
                    else:
                        pattern = "^unmachtable$"

                    plugins[name]["pattern"] = pattern

                    try:
                        plugins[name]["re"] = re.compile(pattern)
                    except:
                        self.log.error(_("%s has a invalid pattern.") % name)

                # internals have no config
                if folder == "internal":
                    self.core.config.deleteConfig(name)
                    continue

                config = self.CONFIG.findall(content)
                if config:
                    config = literal_eval(config[0].strip().replace("\n", "").replace("\r", ""))
                    desc = self.DESC.findall(content)
                    desc = desc[0][1] if desc else ""

                    if type(config) == list and all(type(c) == tuple for c in config):
                        config = dict((x[0], x[1:]) for x in config)
                    else:
                        self.log.error("Invalid config in %s: %s" % (name, config))
                        continue

                    if folder == "hooks" and "activated" not in config:
                            config['activated'] = ["bool", "Activated", False]

                    config['desc'] = desc
                    configs[name] = config

                elif folder == "hooks":  # force config creation
                    desc = self.DESC.findall(content)
                    desc = desc[0][1] if desc else ""
                    config['activated'] = ["bool", "Activated", False]

                    config['desc'] = desc
                    configs[name] = config

        if not home:
            temp_plugins, temp_configs = self.parse(folder, pattern, plugins or True)
            plugins.update(temp_plugins)
            configs.update(temp_configs)

        return plugins, configs


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

    def findPlugin(self, name, pluginlist=("hoster", "crypter", "container")):
        for ptype in pluginlist:
            if name in self.plugins[ptype]:
                return self.plugins[ptype][name], ptype
        return None, None

    def getPlugin(self, name, original=False):
        """return plugin module from hoster|decrypter|container"""
        plugin, type = self.findPlugin(name)

        if not plugin:
            self.log.warning("Plugin %s not found." % name)
            plugin = self.hosterPlugins["BasePlugin"]

        if "new_module" in plugin and not original:
            return plugin["new_module"]

        return self.loadModule(type, name)

    def getPluginName(self, name):
        """ used to obtain new name if other plugin was injected"""
        plugin, type = self.findPlugin(name)

        if "new_name" in plugin:
            return plugin["new_name"]

        return name

    def loadModule(self, type, name):
        """ Returns loaded module for plugin

        :param type: plugin type, subfolder of module.plugins
        :param name:
        """
        plugins = self.plugins[type]
        if name in plugins:
            if "module" in plugins[name]: return plugins[name]["module"]
            try:
                module = __import__(self.ROOT + "%s.%s" % (type, plugins[name]["name"]), globals(), locals(),
                    plugins[name]["name"])
                plugins[name]["module"] = module  #cache import, maybe unneeded
                return module
            except Exception, e:
                self.log.error(_("Error importing %(name)s: %(msg)s") % {"name": name, "msg": str(e)})
                if self.core.debug:
                    print_exc()
        else:
            self.log.debug("Plugin %s not found" % name)
            self.log.debug("Available plugins : %s" % str(plugins))

    def loadClass(self, type, name):
        """Returns the class of a plugin with the same name"""
        module = self.loadModule(type, name)
        if module: return getattr(module, name)

    def getAccountPlugins(self):
        """return list of account plugin names"""
        return self.accountPlugins.keys()

    def find_module(self, fullname, path=None):
        #redirecting imports if necesarry
        if fullname.startswith(self.ROOT) or fullname.startswith(self.USERROOT): #seperate pyload plugins
            if fullname.startswith(self.USERROOT): user = 1
            else: user = 0 #used as bool and int

            split = fullname.split(".")
            if len(split) != 4 - user: return
            type, name = split[2 - user:4 - user]

            if type in self.plugins and name in self.plugins[type]:
                #userplugin is a newer version
                if not user and self.plugins[type][name]["user"]:
                    return self
                #imported from userdir, but pyloads is newer
                if user and not self.plugins[type][name]["user"]:
                    return self


    def load_module(self, name, replace=True):
        if name not in sys.modules:  #could be already in modules
            if replace:
                if self.ROOT in name:
                    newname = name.replace(self.ROOT, self.USERROOT)
                else:
                    newname = name.replace(self.USERROOT, self.ROOT)
            else: newname = name

            base, plugin = newname.rsplit(".", 1)

            self.log.debug("Redirected import %s -> %s" % (name, newname))

            module = __import__(newname, globals(), locals(), [plugin])
            #inject under new an old name
            sys.modules[name] = module
            sys.modules[newname] = module

        return sys.modules[name]


    def reloadPlugins(self, type_plugins):
        """ reloads and reindexes plugins """

        def merge(dst, src, overwrite=False):
            """merge dict of dicts"""
            for name in src:
                if name in dst:
                    if overwrite is True:
                        dst[name].update(src[name])
                    else:
                        for _k in set(src[name].keys()) - set(dst[name].keys()):
                            dst[name][_k] = src[name][_k]
                else:
                    dst[name] = src[name]


        if not type_plugins: return False

        self.log.debug("Request reload of plugins: %s" % type_plugins)

        as_dict = {}
        for t,n in type_plugins:
            if t in as_dict:
                as_dict[t].append(n)
            else:
                as_dict[t] = [n]

        # we do not reload hooks or internals, would cause to much side effects
        if "hooks" in as_dict or "internal" in as_dict:
            return False

        for type in as_dict.iterkeys():
            for plugin in as_dict[type]:
                if plugin in self.plugins[type]:
                    if "module" in self.plugins[type][plugin]:
                        self.log.debug("Reloading %s" % plugin)
                        reload(self.plugins[type][plugin]["module"])

        #index creation
        self.crypterPlugins , config = self.parse("crypter", pattern=True)
        self.plugins["crypter"] = self.crypterPlugins
        default_config = config

        self.containerPlugins, config = self.parse("container", pattern=True)
        self.plugins["container"] = self.containerPlugins
        merge(default_config, config)

        self.hosterPlugins, config = self.parse("hoster", pattern=True)
        self.plugins["hoster"] = self.hosterPlugins
        merge(default_config, config)

        self.captchaPlugins, config = self.parse("captcha")
        self.plugins["captcha"] = self.captchaPlugins
        merge(default_config, config)

        self.accountPlugins, config = self.parse("accounts")
        self.plugins["accounts"] = self.accountPlugins
        merge(default_config, config)

        for name, config in default_config.items():
            desc = config.pop('desc', "")
            config = [[k] + list(v) for k, v in config.items()]
            try:
                self.core.config.addPluginConfig(name, config, desc)
            except:
                self.log.error("Invalid config in %s: %s" % (name, config))

        if "accounts" in as_dict: #accounts needs to be reloaded
            self.core.accountManager.initPlugins()
            self.core.scheduler.addJob(0, self.core.accountManager.getAccountInfos)

        return True



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
    
