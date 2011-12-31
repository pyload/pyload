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
from os.path import isfile, join, exists, abspath, basename
from sys import version_info
from time import time
from traceback import print_exc

from module.lib.SafeEval import const_eval as literal_eval
from module.plugins.Base import Base

from new_collections import namedtuple

# ignore these plugin configs, mainly because plugins were wiped out
IGNORE = (
    "FreakshareNet", "SpeedManager", "ArchiveTo", "ShareCx", ('hooks', 'UnRar'),
    'EasyShareCom', 'FlyshareCz'
    )

PluginTuple = namedtuple("PluginTuple", "version re deps user path")

class PluginManager:
    ROOT = "module.plugins."
    USERROOT = "userplugins."
    TYPES = ("crypter", "hoster", "captcha", "accounts", "hooks", "internal")

    SINGLE = re.compile(r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(?:r|u|_)?((?:(?<!")"(?!")|\'|\().*(?:(?<!")"(?!")|\'|\)))',
        re.I)

    # note the nongreedy character, that means we can not embed list and dicts
    MULTI = re.compile(r'__(?P<attr>[a-z0-9_]+)__\s*=\s*((?:\{|\[|"{3}).*?(?:"""|\}|\]))', re.DOTALL | re.M | re.I)

    def __init__(self, core):
        self.core = core

        #self.config = self.core.config
        self.log = core.log

        self.plugins = {}
        self.modules = {} # cached modules
        self.names = {} # overwritten names
        self.history = []  # match history to speedup parsing (type, name)
        self.createIndex()


        self.core.config.parseValues(self.core.config.PLUGIN)

        #register for import hook
        sys.meta_path.append(self)


    def logDebug(self, type, plugin, msg):
        self.log.debug("Plugin %s | %s: %s" % (type, plugin, msg))

    def createIndex(self):
        """create information for all plugins available"""
        # add to path, so we can import from userplugins
        sys.path.append(abspath(""))

        if not exists("userplugins"):
            makedirs("userplugins")
        if not exists(join("userplugins", "__init__.py")):
            f = open(join("userplugins", "__init__.py"), "wb")
            f.close()

        a = time()
        for type in self.TYPES:
            self.plugins[type] = self.parse(type)

        self.log.debug("Created index of plugins in %.2f ms", (time() - a) * 1000)

    def parse(self, folder, home=None):
        """  Analyze and parses all plugins in folder """
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
                if f.endswith("_25.pyc") and version_info[0:2] != (2, 5):
                    continue
                elif f.endswith("_26.pyc") and version_info[0:2] != (2, 6):
                    continue
                elif f.endswith("_27.pyc") and version_info[0:2] != (2, 7):
                    continue

                # replace suffix and version tag
                name = f[:-3]
                if name[-1] == ".": name = name[:-4]

                plugin = self.parsePlugin(join(pfolder, f), folder, name, home)
                if plugin:
                    plugins[name] = plugin

        if not home:
            temp = self.parse(folder, plugins)
            plugins.update(temp)

        return plugins

    def parsePlugin(self, filename, folder, name, home=None):
        """  Parses a plugin from disk, folder means plugin type in this context. Also sets config.

        :arg home: dict with plugins, of which the found one will be matched against (according version)
        :returns PluginTuple"""

        data = open(filename, "rb")
        content = data.read()
        data.close()

        attrs = {}
        for m in self.SINGLE.findall(content) + self.MULTI.findall(content):
            #replace gettext function and eval result
            try:
                attrs[m[0]] = literal_eval(m[-1].replace("_(", "("))
            except:
                self.logDebug(folder, name, "Error when parsing: %s" % m[-1])
                return
            if not hasattr(Base, "__%s__" % m[0]):
                if m[0] != "type": #TODO remove type from all plugins, its not needed
                    self.logDebug(folder, name, "Unknown attribute '%s'" % m[0])

        version = 0

        if "version" in attrs:
            try:
                version = float(attrs["version"])
            except ValueError:
                self.logDebug(folder, name, "Invalid version %s" % attrs["version"])
                version = 9 #TODO remove when plugins are fixed, causing update loops
        else:
            self.logDebug(folder, name, "No version attribute")

        # home contains plugins from pyload root
        if home and name in home:
            if home[name].version >= version:
                return

        if name in IGNORE or (folder, name) in IGNORE:
            return

        if "pattern" in attrs and attrs["pattern"]:
            try:
                plugin_re = re.compile(attrs["pattern"])
            except:
                self.logDebug(folder, name, "Invalid regexp pattern '%s'" % attrs["pattern"])
                plugin_re = None
        else: plugin_re = None

        deps = attrs.get("dependencies", None)

        # create plugin tuple
        plugin = PluginTuple(version, plugin_re, deps, bool(home), filename)


        # internals have no config
        if folder == "internal":
            return plugin

        if folder == "hooks" and "config" not in attrs:
            attrs["config"] = (["activated", "bool", "Activated", False],)

        if "config" in attrs and attrs["config"]:
            config = attrs["config"]
            desc = attrs.get("description", "")
            long_desc = attrs.get("long_description", "")

            if type(config[0]) == tuple:
                config = [list(x) for x in config]
            else:
                config = [list(config)]

            if folder == "hooks":
                append = True
                for item in config:
                    if item[0] == "activated": append = False

                # activated flag missing
                if append: config.insert(0, ("activated", "bool", "Activated", False))

            try:
                self.core.config.addConfigSection(name, name, desc, long_desc, config)
            except:
                self.logDebug(folder, name, "Invalid config  %s" % config)

        return plugin


    def parseUrls(self, urls):
        """parse plugins for given list of urls, seperate to crypter and hoster"""

        res = {"hoster": [], "crypter": []} # tupels of (url, plugin)

        for url in urls:
            if type(url) not in (str, unicode, buffer):
                self.log.debug("Parsing invalid type %s" % type(url))
                continue

            found = False

            for ptype, name in self.history:
                if self.plugins[ptype][name].re.match(url):
                    res[ptype].append((url, name))
                    found = (ptype, name)
                    break

            if found:  # found match
                if self.history[0] != found: #update history
                    self.history.remove(found)
                    self.history.insert(0, found)
                continue

            for ptype in ("crypter", "hoster"):
                for name, plugin in self.plugins[ptype].iteritems():
                    if plugin.re.match(url):
                        res[ptype].append((url, name))
                        self.history.insert(0, (ptype, name))
                        del self.history[10:] # cut down to size of 10
                        found = True
                        break

            if not found:
                res["hoster"].append((url, "BasePlugin"))

        return res["hoster"], res["crypter"]

    def getPlugins(self, type):
        return self.plugins.get(type, None)

    def findPlugin(self, name, pluginlist=("hoster", "crypter")):
        for ptype in pluginlist:
            if name in self.plugins[ptype]:
                return ptype, self.plugins[ptype][name]
        return None, None

    def getPlugin(self, name, original=False):
        """return plugin module from hoster|decrypter"""
        type, plugin = self.findPlugin(name)

        if not plugin:
            self.log.warning("Plugin %s not found." % name)
            name = "BasePlugin"

        if (type, name) in self.modules and not original:
            return self.modules[(type, name)]

        return self.loadModule(type, name)

    def getPluginName(self, name):
        """ used to obtain new name if other plugin was injected"""
        type, plugin = self.findPlugin(name)

        if (type, name) in self.names:
            return self.names[(type, name)]

        return name

    def loadModule(self, type, name):
        """ Returns loaded module for plugin

        :param type: plugin type, subfolder of module.plugins
        :param name:
        """
        plugins = self.plugins[type]
        if name in plugins:
            if (type, name) in self.modules: return self.modules[(type, name)]
            try:
                # convert path to python recognizable import
                path = basename(plugins[name].path).replace(".pyc", "").replace(".py", "")
                module = __import__(self.ROOT + "%s.%s" % (type, path), globals(), locals(), path)
                self.modules[(type, name)] = module # cache import, maybe unneeded
                return module
            except Exception, e:
                self.log.error(_("Error importing %(name)s: %(msg)s") % {"name": name, "msg": str(e)})
                if self.core.debug:
                    print_exc()

    def loadClass(self, type, name):
        """Returns the class of a plugin with the same name"""
        module = self.loadModule(type, name)
        if module: return getattr(module, name)

    def injectPlugin(self, type, name, module, new_name):
        """ Overwrite a plugin with a other module. used by Multihoster """
        self.modules[(type, name)] = module
        self.names[(type, name)] = new_name

    def restoreState(self, type, name):
        """ Restore the state of a plugin after injecting """
        if (type, name) in self.modules:
            del self.modules[(type, name)]
        if (type, name) in self.names:
            del self.names[(type, name)]

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
                if not user and self.plugins[type][name].user:
                    return self
                    #imported from userdir, but pyloads is newer
                if user and not self.plugins[type][name].user:
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
        if not type_plugins: return False

        self.log.debug("Request reload of plugins: %s" % type_plugins)

        as_dict = {}
        for t, n in type_plugins:
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
                    if (type, plugin) in self.modules:
                        self.log.debug("Reloading %s" % plugin)
                        reload(self.modules[(type, plugin)])

        # index re-creation
        for type in ("crypter", "container", "hoster", "captcha", "accounts"):
            self.plugins[type] = self.parse(type)

        if "accounts" in as_dict: #accounts needs to be reloaded
            self.core.accountManager.initPlugins()
            self.core.scheduler.addJob(0, self.core.accountManager.getAccountInfos)

        return True

    def loadIcons(self):
        """Loads all icons from plugins, plugin type is not in result, because its not important here.

        :return: Dict of names mapped to icons
        """
        pass

    def loadIcon(self, type, name):
        """ load icon for single plugin, base64 encoded"""
        pass

    def checkDependencies(self, type, name):
        """ Check deps for given plugin

        :return: List of unfullfilled dependencies
        """
        pass
    
