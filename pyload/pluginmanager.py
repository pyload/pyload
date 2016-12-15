# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals
from builtins import str
from builtins import object
from builtins import pypath
import sys

from os.path import abspath, join
from pyload.utils.pluginloader import LoaderFactory, PluginLoader


class PluginMatcher(object):
    """ Abstract class that allows modify which plugins to match and to load """

    def matchURL(self, url):
        """ Returns (type, name) of a plugin if a match is found  """
        return

    def matchPlugin(self, plugin, name):
        """ Returns (type, name) of the plugin that will be loaded instead """
        return None


class PluginManager(object):
    ROOT = "pyload.plugins"
    LOCALROOT = "localplugins"

    MATCH_HISTORY = 10
    DEFAULT_PLUGIN = "BasePlugin"

    def __init__(self, core):
        self.pyload = core
        self.log = core.log

        # cached modules (type, name)
        self.modules = {}
        # match history to speedup parsing (type, name)
        self.history = []

        #register for import addon
        sys.meta_path.append(self)

        # add to path, so we can import from userplugins
        sys.path.append(abspath(""))
        self.loader = LoaderFactory(PluginLoader(abspath(self.LOCALROOT), self.LOCALROOT, self.pyload.config),
                                    PluginLoader(abspath(join(pypath, "pyload", "plugins")), self.ROOT,
                                                 self.pyload.config))

        self.loader.checkVersions()

        # plugin matcher to overwrite some behaviour
        self.matcher = []

    def addMatcher(self, matcher, index=0):
        """ Inserts matcher at given index, first position by default """
        if not isinstance(matcher, PluginMatcher):
            raise TypeError("Expected type of PluginMatcher, got '%s' instead" % type(matcher))

        if matcher in self.matcher:
            self.matcher.remove(matcher)

        self.matcher.insert(index, matcher)

    def removeMatcher(self, matcher):
        """ Removes a matcher if it exists """
        if matcher in self.matcher:
            self.matcher.remove(matcher)

    def parseUrls(self, urls):
        """parse plugins for given list of urls, separate to crypter and hoster"""

        res = {"hoster": [], "crypter": []} # tupels of (url, plugin)

        for url in urls:
            if type(url) not in (str, buffer):
                self.log.debug("Parsing invalid type %s" % type(url))
                continue

            found = False

            # search the history
            for ptype, name in self.history:
                if self.loader.getPlugin(ptype, name).re.match(url):
                    res[ptype].append((url, name))
                    found = (ptype, name)
                    break # need to exit this loop first

            if found:  # found match
                if self.history[0] != found: #update history
                    self.history.remove(found)
                    self.history.insert(0, found)
                continue

            # matcher are tried secondly, they won't go to history
            for m in self.matcher:
                match = m.matchURL(url)
                if match and match[0] in res:
                    ptype, name = match
                    res[ptype].append((url, name))
                    found = True
                    break

            if found:
                continue

            for ptype in ("crypter", "hoster"):
                for loader in self.loader:
                    for name, plugin in loader.getPlugins(ptype).items():
                        if plugin.re.match(url):
                            res[ptype].append((url, name))
                            self.history.insert(0, (ptype, name))
                            del self.history[self.MATCH_HISTORY:] # cut down to size
                            found = True
                            break
                    if found: break
                if found: break

            if not found:
                res["hoster"].append((url, self.DEFAULT_PLUGIN))

        return res["hoster"], res["crypter"]

    def findPlugin(self, name):
        """ Finds the type to a plugin name """
        return self.loader.findPlugin(name)

    def getPlugin(self, plugin, name):
        """ Retrieves the plugin tuple for a single plugin or none """
        return self.loader.getPlugin(plugin, name)

    def getPlugins(self, plugin):
        """  Get all plugins of a certain type in a dict """
        plugins = {}
        for loader in self.loader:
            plugins.update(loader.getPlugins(plugin))
        return plugins

    def getPluginClass(self, plugin, name, overwrite=True):
        """Gives the plugin class of a hoster or crypter plugin

        :param overwrite: allow the use of overwritten plugins
        """
        if overwrite:
            for m in self.matcher:
                match = m.matchPlugin(plugin, name)
                if match:
                    plugin, name = match

        return self.loadClass(plugin, name)

    def loadAttributes(self, plugin, name):
        for loader in self.loader:
            if loader.hasPlugin(plugin, name):
                return loader.loadAttributes(plugin, name)

        return {}

    def loadModule(self, plugin, name):
        """ Returns loaded module for plugin

        :param plugin: plugin type, subfolder of module.plugins
        """
        if (plugin, name) in self.modules: return self.modules[(plugin, name)]
        for loader in self.loader:
            if loader.hasPlugin(plugin, name):
                try:
                    module = loader.loadModule(plugin, name)
                    # cache import
                    self.modules[(plugin, name)] = module
                    return module
                except Exception as e:
                    self.log.error(_("Error importing %(name)s: %(msg)s") % {"name": name, "msg": str(e)})
                    self.pyload.print_exc()

    def loadClass(self, plugin, name):
        """Returns the class of a plugin with the same name"""
        module = self.loadModule(plugin, name)
        try:
            if module: return getattr(module, name)
        except AttributeError:
            self.log.error(_("Plugin does not define class '%s'") % name)

    def find_module(self, fullname, path=None):
        #redirecting imports if necessary
        for loader in self.loader:
            if not fullname.startswith(loader.package):
                continue

            # TODO not well tested
            offset = 1 - loader.package.count(".")

            split = fullname.split(".")
            if len(split) != 4 - offset: return
            plugin, name = split[2 - offset:4 - offset]

            # check if a different loader than the current one has the plugin
            # in this case import needs redirect
            for l2 in self.loader:
                if l2 is not loader and l2.hasPlugin(plugin, name):
                    return self

        # TODO: Remove when all plugin imports are adapted
        if "module" in fullname:
            return self

    def load_module(self, name, replace=True):
        if name not in sys.modules:  #could be already in modules

            # TODO: only temporary
            # TODO: strange side effects are caused by this workaround
            # e.g a class instance is not associated correctly with its on instance because of wrong module names
            if name.endswith("module"):
                # name = "pyload."
                name = name.replace(".module", "")
                self.log.debug("Old import reference detected, use %s" % name)
                replace = False
                return __import__("pyload")
            if name.startswith("module"):
                name = name.replace("module", "pyload")
                self.log.debug("Old import reference detected, use %s" % name)
                replace = False

            # TODO: this still works but does not respect other loaders
            if replace:
                if self.ROOT in name:
                    newname = name.replace(self.ROOT, self.LOCALROOT)
                else:
                    newname = name.replace(self.LOCALROOT, self.ROOT)
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
        # TODO
        # check if reloadable
        # reload
        # save new plugins
        # update index
        # reload accounts

    def isUserPlugin(self, plugin):
        """ A plugin suitable for multiple user """
        return any(l.isUserPlugin(plugin) for l in self.loader)

    def getCategory(self, plugin):
        plugin = self.loader.getPlugin("addon", plugin)
        if plugin:
            return plugin.category or "addon"

    def loadIcon(self, name):
        """ load icon for single plugin, base64 encoded"""
        pass

    def checkDependencies(self, type, name):
        """ Check deps for given plugin

        :return: List of unfullfilled dependencies
        """
        pass
