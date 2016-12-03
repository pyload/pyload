###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

import re

from os import listdir, makedirs
from os.path import isfile, join, exists, basename
from sys import version_info
from time import time
from collections import defaultdict
from logging import getLogger

from pyload.lib.SafeEval import const_eval as literal_eval
from pyload.plugins.Base import Base

from new_collections import namedtuple

PluginTuple = namedtuple("PluginTuple", "version re deps category user path")


class BaseAttributes(defaultdict):
    """ Dictionary that loads defaults values from Base object """

    def __missing__(self, key):
        attr = "__%s__" % key
        if not hasattr(Base, attr):
            return defaultdict.__missing__(self, key)

        return getattr(Base, attr)


class LoaderFactory:
    """ Container for multiple plugin loaders  """

    def __init__(self, *loader):
        self.loader = list(loader)

    def __iter__(self):
        return self.loader.__iter__()


    def checkVersions(self):
        """ Reduces every plugin loader to the globally newest version.
        Afterwards every plugin is unique across all available loader """
        for plugin_type in self.loader[0].iterTypes():
            for loader in self.loader:
                # iterate all plugins
                for plugin, info in loader.getPlugins(plugin_type).items():
                    # now iterate all other loaders
                    for l2 in self.loader:
                        if l2 is not loader:
                            l2.removePlugin(plugin_type, plugin, info.version)

    def findPlugin(self, name):
        """ Finds a plugin type for given name """
        for loader in self.loader:
            for t in loader.TYPES:
                if loader.hasPlugin(t, name):
                    return t

        return None

    def getPlugin(self, plugin, name):
        """ retrieve a plugin from an available loader """
        for loader in self.loader:
            if loader.hasPlugin(plugin, name):
                return loader.getPlugin(plugin, name)


class PluginLoader:
    """
    Class to provide and load plugins from the file-system
    """
    TYPES = ("crypter", "hoster", "accounts", "addons", "network", "internal")

    BUILTIN = re.compile(r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(True|False|None|[0-9x.]+)', re.I)
    SINGLE = re.compile(r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(?:r|u|_)?((?:(?<!")"(?!")|\').*(?:(?<!")"(?!")|\'))',
                        re.I)
    # finds the beginning of a expression that could span multiple lines
    MULTI = re.compile(r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(\(|\{|\[|"{3})', re.I)

    # closing symbols
    MULTI_MATCH = {
        "{": "}",
        "(": ")",
        "[": "]",
        '"""': '"""'
    }

    NO_MATCH = re.compile(r'^no_match$')

    def __init__(self, path, package, config):
        self.path = path
        self.package = package
        self.config = config
        self.log = getLogger("log")
        self.plugins = {}

        self.createIndex()

    def logDebug(self, plugin, name, msg):
        self.log.debug("Plugin %s | %s: %s" % (plugin, name, msg))

    def createIndex(self):
        """create information for all plugins available"""

        if not exists(self.path):
            makedirs(self.path)
        if not exists(join(self.path, "__init__.py")):
            f = open(join(self.path, "__init__.py"), "wb")
            f.close()

        a = time()
        for plugin in self.TYPES:
            self.plugins[plugin] = self.parse(plugin)

        self.log.debug("Created index of plugins for %s in %.2f ms", self.path, (time() - a) * 1000)

    def parse(self, folder):
        """  Analyze and parses all plugins in folder """
        plugins = {}
        pfolder = join(self.path, folder)
        if not exists(pfolder):
            makedirs(pfolder)
        if not exists(join(pfolder, "__init__.py")):
            f = open(join(pfolder, "__init__.py"), "wb")
            f.close()

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

                plugin = self.parsePlugin(join(pfolder, f), folder, name)
                if plugin:
                    plugins[name] = plugin

        return plugins

    def parseAttributes(self, filename, name, folder=""):
        """ Parse attribute dict from plugin"""
        data = open(filename, "rb")
        content = data.read()
        data.close()

        attrs = BaseAttributes()
        for m in self.BUILTIN.findall(content) + self.SINGLE.findall(content) + self.parseMultiLine(content):
            #replace gettext function and eval result
            try:
                attrs[m[0]] = literal_eval(m[-1].replace("_(", "("))
            except Exception as e:
                self.logDebug(folder, name, "Error when parsing: %s" % m[-1])
                self.log.debug(str(e))

            if not hasattr(Base, "__%s__" % m[0]):
                #TODO remove type from all plugins, its not needed
                if m[0] != "type" and m[0] != "author_name":
                    self.logDebug(folder, name, "Unknown attribute '%s'" % m[0])

        return attrs

    def parseMultiLine(self, content):
        # regexp is not enough to parse multi line statements
        attrs = []
        for m in self.MULTI.finditer(content):
            attr = m.group(1)
            char = m.group(2)
            # the end char to search for
            endchar = self.MULTI_MATCH[char]
            size = len(endchar)
            # save number of of occurred
            stack = 0
            endpos = m.start(2) - size

            #TODO: strings must be parsed too, otherwise breaks very easily
            for i in range(m.end(2), len(content) - size + 1):
                if content[i:i + size] == endchar:
                    # closing char seen and match now complete
                    if stack == 0:
                        endpos = i
                        break
                    else:
                        stack -= 1
                elif content[i:i + size] == char:
                    stack += 1

            # in case the end was not found match will be empty
            attrs.append((attr, content[m.start(2): endpos + size]))

        return attrs


    def parsePlugin(self, filename, folder, name):
        """  Parses a plugin from disk, folder means plugin type in this context. Also sets config.

        :arg home: dict with plugins, of which the found one will be matched against (according version)
        :returns PluginTuple"""

        attrs = self.parseAttributes(filename, name, folder)
        if not attrs: return

        version = 0
        if "version" in attrs:
            try:
                version = float(attrs["version"])
            except ValueError:
                self.logDebug(folder, name, "Invalid version %s" % attrs["version"])
                version = 9 #TODO remove when plugins are fixed, causing update loops
        else:
            self.logDebug(folder, name, "No version attribute")

        if "pattern" in attrs and attrs["pattern"]:
            try:
                plugin_re = re.compile(attrs["pattern"], re.I)
            except:
                self.logDebug(folder, name, "Invalid regexp pattern '%s'" % attrs["pattern"])
                plugin_re = self.NO_MATCH
        else:
            plugin_re = self.NO_MATCH

        deps = attrs["dependencies"]
        category = attrs["category"] if folder == "addons" else ""

        # create plugin tuple
        # user_context=True is the default for non addons plugins
        plugin = PluginTuple(version, plugin_re, deps, category,
                             bool(folder != "addons" or attrs["user_context"]), filename)

        # These have none or their own config
        if folder in ("internal", "accounts", "network"):
            return plugin

        if folder == "addons" and "config" not in attrs and not attrs["internal"]:
            attrs["config"] = (["activated", "bool", "Activated", False],)

        if "config" in attrs and attrs["config"] is not None:
            config = attrs["config"]
            desc = attrs["description"]
            expl = attrs["explanation"]

            # Convert tuples to list
            config = [list(x) for x in config]

            if folder == "addons" and not attrs["internal"]:
                for item in config:
                    if item[0] == "activated": break
                else: # activated flag missing
                    config.insert(0, ("activated", "bool", "Activated", False))

            try:
                self.config.addConfigSection(name, name, desc, expl, config)
            except:
                self.logDebug(folder, name, "Invalid config  %s" % config)

        return plugin

    def iterPlugins(self):
        """ Iterates over all plugins returning (type, name, info)  with info as PluginTuple """

        for plugin, data in self.plugins.items():
            for name, info in data.items():
                yield plugin, name, info

    def iterTypes(self):
        """ Iterate over the available plugin types """

        for plugin in self.plugins.keys():
            yield plugin

    def hasPlugin(self, plugin, name):
        """ Check if certain plugin is available """
        return plugin in self.plugins and name in self.plugins[plugin]

    def getPlugin(self, plugin, name):
        """  Return plugin info for a single entity """
        try:
            return self.plugins[plugin][name]
        except KeyError:
            return None

    def getPlugins(self, plugin):
        """ Return all plugins of given plugin type """
        return self.plugins[plugin]

    def removePlugin(self, plugin, name, available_version=None):
        """ Removes a plugin from the index.
         Optionally only when its version is below or equal the available one
         """
        try:
            if available_version is not None:
                if self.plugins[plugin][name] <= available_version:
                    del self.plugins[plugin][name]
            else:
                del self.plugins[plugin][name]

        # no errors are thrown if the plugin didn't existed
        except KeyError:
            return

    def isUserPlugin(self, name):
        """ Determine if given plugin name is enable for user_context in any plugin type """
        for plugins in self.plugins:
            if name in plugins and name[plugins].user:
                return True

        return False

    def savePlugin(self, content):
        """ Saves a plugin to disk  """

    def loadModule(self, plugin, name):
        """ Returns loaded module for plugin

        :param plugin: plugin type, subfolder of module.plugins
        :raises Exception: Everything could go wrong, failures needs to be catched
        """
        plugins = self.plugins[plugin]
        # convert path to python recognizable import
        path = basename(plugins[name].path).replace(".pyc", "").replace(".py", "")
        module = __import__(self.package + ".%s.%s" % (plugin, path), globals(), locals(), path)
        return module

    def loadAttributes(self, plugin, name):
        """ Same as `parseAttributes` for already indexed plugins  """
        return self.parseAttributes(self.plugins[plugin][name].path, name, plugin)
