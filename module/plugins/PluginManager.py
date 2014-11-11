# -*- coding: utf-8 -*-

import re
import sys

from itertools import chain
from os import listdir, makedirs
from os.path import isfile, join, exists, abspath
from sys import version_info
from traceback import print_exc

from module.lib.SafeEval import const_eval as literal_eval

from module.ConfigParser import IGNORE


class PluginManager:
    ROOT     = "module.plugins."
    USERROOT = "userplugins."
    TYPES    = ("crypter", "container", "hoster", "captcha", "accounts", "hooks", "internal")

    PATTERN = re.compile(r'__pattern__\s*=\s*u?r("|\')([^"\']+)')
    VERSION = re.compile(r'__version__\s*=\s*("|\')([\d.]+)')
    CONFIG  = re.compile(r'__config__\s*=\s*\[([^\]]+)', re.M)
    DESC    = re.compile(r'__description__\s*=\s*("|"""|\')([^"\']+)')


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

        sys.path.append(abspath(""))

        #@NOTE: In 0.4.10 directory "accounts" changes to "account" and "hooks" changes to "hook"
        self.plugins['accounts'] = self.accountPlugins = self.parse("accounts")
        self.plugins['hooks']    = self.hookPlugins    = self.parse("hooks")

        for type in ('captcha', 'container', 'crypter', 'hoster', 'internal'):
            self.plugins[type] = self.parse(type)
            setattr(self, "%sPlugins" % type, self.plugins[type])

        self.log.debug("Created index of plugins")


    def parse(self, folder, rootplugins={}):
        """
        returns dict with information
        home contains parsed plugins from module.

        {
        name : {path, version, config, (pattern, re), (plugin, class)}
        }

        """

        plugins = {}

        if rootplugins:
            try:
                pfolder = join("userplugins", folder)
                if not exists(pfolder):
                    makedirs(pfolder)

                for ifile in (join("userplugins", "__init__.py"),
                              join(pfolder, "__init__.py")):
                    if not exists(ifile):
                        f = open(ifile, "wb")
                        f.close()

            except IOError, e:
                self.logCritical(e)
                return rootplugins

        else:
            pfolder = join(pypath, "module", "plugins", folder)

        for f in listdir(pfolder):
            if (isfile(join(pfolder, f)) and f.endswith(".py") or f.endswith("_25.pyc") or f.endswith(
                "_26.pyc") or f.endswith("_27.pyc")) and not f.startswith("_"):

                try:
                    with open(join(pfolder, f)) as data:
                        content = data.read()

                except IOError, e:
                    self.logError(e)
                    continue

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

                if rootplugins and name in rootplugins:
                    if rootplugins[name]['v'] >= version:
                        continue

                if name in IGNORE or (folder, name) in IGNORE:
                     continue

                plugins[name] = {}
                plugins[name]['v'] = version

                module = f.replace(".pyc", "").replace(".py", "")

                # the plugin is loaded from user directory
                plugins[name]['user'] = True if rootplugins else False
                plugins[name]['name'] = module

                pattern = self.PATTERN.findall(content)

                if pattern:
                    pattern = pattern[0][1]

                    plugins[name]['pattern'] = pattern

                    try:
                        plugins[name]['re'] = re.compile(pattern)
                    except:
                        self.log.error(_("%s has a invalid pattern") % name)

                # internals have no config
                if folder == "internal":
                    self.core.config.deleteConfig(name)
                    continue

                config = self.CONFIG.findall(content)
                if config:
                    try:
                        config = literal_eval(config[0].strip().replace("\n", "").replace("\r", ""))
                        desc = self.DESC.findall(content)
                        desc = desc[0][1] if desc else ""

                        if type(config[0]) == tuple:
                            config = [list(x) for x in config]
                        else:
                            config = [list(config)]

                        if folder not in ("accounts", "internal") and not [True for item in config if item[0] == "activated"]:
                            config.insert(0, ["activated", "bool", "Activated", False if folder == "hooks" else True])

                        self.core.config.addPluginConfig(name, config, desc)
                    except:
                        self.log.error("Invalid config in %s: %s" % (name, config))

                elif folder == "hooks": #force config creation
                    desc = self.DESC.findall(content)
                    desc = desc[0][1] if desc else ""
                    config = (["activated", "bool", "Activated", False],)

                    try:
                        self.core.config.addPluginConfig(name, config, desc)
                    except:
                        self.log.error("Invalid config in %s: %s" % (name, config))

        if not rootplugins and plugins:  #: Double check
            plugins.update(self.parse(folder, plugins))

        return plugins


    def parseUrls(self, urls):
        """parse plugins for given list of urls"""

        last = None
        res = [] # tupels of (url, plugin)

        for url in urls:
            if type(url) not in (str, unicode, buffer): continue
            found = False

            if last and last[1]['re'].match(url):
                res.append((url, last[0]))
                continue

            for name, value in chain(self.crypterPlugins.iteritems(), self.hosterPlugins.iteritems(),
                self.containerPlugins.iteritems()):
                if value['re'].match(url):
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
            self.log.warning("Plugin %s not found" % name)
            plugin = self.hosterPlugins['BasePlugin']

        if "new_module" in plugin and not original:
            return plugin['new_module']

        return self.loadModule(type, name)


    def getPluginName(self, name):
        """ used to obtain new name if other plugin was injected"""
        plugin, type = self.findPlugin(name)

        if "new_name" in plugin:
            return plugin['new_name']

        return name


    def loadModule(self, type, name):
        """ Returns loaded module for plugin

        :param type: plugin type, subfolder of module.plugins
        :param name:
        """
        plugins = self.plugins[type]
        if name in plugins:
            if "module" in plugins[name]:
                return plugins[name]['module']

            try:
                module = __import__(self.ROOT + "%s.%s" % (type, plugins[name]['name']), globals(), locals(),
                                    plugins[name]['name'])
                plugins[name]['module'] = module  #cache import, maybe unneeded

            except Exception, e:
                self.log.error(_("Error importing %(name)s: %(msg)s") % {"name": name, "msg": str(e)})
                if self.core.debug:
                    print_exc()

            else:
                self.log.debug(_("Loaded module %(name)s (v%(version).2f)") % {'name': name, 'version': plugins[name]['version']})
                return module


    def loadClass(self, type, name):
        """Returns the class of a plugin with the same name"""
        module = self.loadModule(type, name)
        if module:
            return getattr(module, name)
        else:
            self.log.error(_("%s class %s not loaded") % (type.capitalize(), name))
            return None


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
                if not user and self.plugins[type][name]['user']:
                    return self
                #imported from userdir, but pyloads is newer
                if user and not self.plugins[type][name]['user']:
                    return self


    def load_module(self, name, replace=True):
        if name not in sys.modules:  #could be already in modules
            if replace:
                if self.ROOT in name:
                    newname = name.replace(self.ROOT, self.USERROOT)
                else:
                    newname = name.replace(self.USERROOT, self.ROOT)
            else:
                newname = name

            base, plugin = newname.rsplit(".", 1)

            self.log.debug("Redirected import %s -> %s" % (name, newname))

            module = __import__(newname, globals(), locals(), [plugin])
            #inject under new an old name
            sys.modules[name] = module
            sys.modules[newname] = module

        return sys.modules[name]


    def reloadPlugins(self, type_plugins):
        """ reloads and reindexes plugins """
        if not type_plugins:
            return None

        self.log.debug("Request reload of plugins: %s" % type_plugins)

        flag = True
        as_dict = {}

        for t,n in type_plugins:
            if t in as_dict:
                as_dict[t].append(n)
            else:
                as_dict[t] = [n]

        for type in as_dict.iterkeys():
            # we do not reload hooks or internals, would cause to much side effects
            if type in ("hooks", "internal"):
                flag = False
                continue

            for plugin in as_dict[type]:
                if plugin in self.plugins[type]:
                    if "module" in self.plugins[type][plugin]:
                        self.log.debug("Reloading module %s" % plugin)
                        reload(self.plugins[type][plugin]['module'])

            #index creation
            self.plugins[type] = self.parse(type)

            if type is "accounts":
                self.accountPlugins = self.plugins[type]  #@TODO: Remove in 0.4.10
            else:
                setattr(self, "%sPlugins" % type, self.plugins[type])

        if "accounts" in as_dict:  #: accounts needs to be reloaded
            self.core.accountManager.initPlugins()
            self.core.scheduler.addJob(0, self.core.accountManager.getAccountInfos)

        return flag



if __name__ == "__main__":
    _ = lambda x: x
    pypath = "/home/christian/Projekte/pyload-0.4/module/plugins"

    from time import time

    p = PluginManager(None)

    a = time()

    test = ["http://www.youtube.com/watch?v=%s" % x for x in xrange(0, 100)]
    print p.parseUrls(test)

    b = time()

    print b - a, "s"
