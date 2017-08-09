# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import os
import sys
from builtins import object, str

from future import standard_library
from pkg_resources import resource_filename

from pyload.utils.fs import fullpath

from pyload.core.__about__ import __package__
from pyload.core.manager.base import BaseManager
from pyload.core.network.loader import LoaderFactory, PluginLoader

standard_library.install_aliases()


class PluginMatcher(object):
    """
    Abstract class that allows modify which plugins to match and to load.
    """
    def match_url(self, url):
        """
        Returns (type, name) of a plugin if a match is found.
        """
        return None

    def match_plugin(self, plugin, name):
        """
        Returns (type, name) of the plugin that will be loaded instead.
        """
        return None


class PluginManager(BaseManager):

    ROOT = "pyload.core.plugin"
    LOCALROOT = "userplugins"

    MATCH_HISTORY = 10
    DEFAULT_PLUGIN = "BasePlugin"

    def __init__(self, core):
        BaseManager.__init__(self, core)

        # cached modules (type, name)
        self.modules = {}
        # match history to speedup parsing (type, name)
        self.history = []

        # register for import addon
        sys.meta_path.append(self)

        # add to path, so we can import from userplugins
        sys.path.append(os.getcwd())  # TODO: Recheck...
        self.loader = LoaderFactory(
            PluginLoader(fullpath(self.LOCALROOT),
                         self.LOCALROOT, self.pyload_core.config),
            PluginLoader(resource_filename(__package__, 'network'),
                         self.ROOT, self.pyload_core.config),
        )

        self.loader.check_versions()

        # plugin matcher to overwrite some behaviour
        self.matcher = []

    def add_matcher(self, matcher, index=0):
        """
        Inserts matcher at given index, first position by default.
        """
        if not isinstance(matcher, PluginMatcher):
            raise TypeError(
                "Expected type of PluginMatcher, got '{0}' instead".format(
                    type(matcher)))

        if matcher in self.matcher:
            self.matcher.remove(matcher)

        self.matcher.insert(index, matcher)

    def remove_matcher(self, matcher):
        """
        Removes a matcher if it exists.
        """
        if matcher in self.matcher:
            self.matcher.remove(matcher)

    def parse_urls(self, urls):
        """
        Parse plugins for given list of urls, separate to crypter and hoster.
        """
        res = {'hoster': [], 'crypter': []}  # tupels of (url, plugin)

        for url in urls:
            if not isinstance(url, str):
                self.pyload_core.log.debug(
                    "Parsing invalid type {0}".format(type(url)))
                continue

            found = False

            # search the history
            for ptype, name in self.history:
                if self.loader.get_plugin(ptype, name).re.match(url):
                    res[ptype].append((url, name))
                    found = (ptype, name)
                    break  # need to exit this loop first

            if found:  # found match
                if self.history[0] != found:  # update history
                    self.history.remove(found)
                    self.history.insert(0, found)
                continue

            # matcher are tried secondly, they won't go to history
            for m in self.matcher:
                match = m.match_url(url)
                if match and match[0] in res:
                    ptype, name = match
                    res[ptype].append((url, name))
                    found = True
                    break

            if found:
                continue

            for _type in ("crypter", "hoster"):
                for loader in self.loader:
                    for name, info in loader.get_plugins(_type).items():
                        if info.re.match(url):
                            res[_type].append((url, name))
                            self.history.insert(0, (_type, name))
                            # cut down to size
                            del self.history[self.MATCH_HISTORY:]
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

            if not found:
                res['hoster'].append((url, self.DEFAULT_PLUGIN))

        return res['hoster'], res['crypter']

    def find_type(self, name):
        """
        Finds the type to a plugin name.
        """
        return self.loader.find_type(name)

    def get_plugin(self, type_, name):
        """
        Retrieves the plugin tuple for a single plugin or none.
        """
        return self.loader.get_plugin(type_, name)

    def get_plugins(self, type_):
        """
        Get all plugins of a certain type in a dict.
        """
        plugins = {}
        for loader in self.loader:
            plugins.update(loader.get_plugins(type_))
        return plugins

    def get_plugin_class(self, type_, name, overwrite=True):
        """
        Gives the plugin class of a hoster or crypter plugin

        :param overwrite: allow the use of overwritten plugins
        """
        if overwrite:
            for m in self.matcher:
                match = m.match_plugin(type_, name)
                if match:
                    type_, name = match
        return self.load_class(type_, name)

    def load_attributes(self, type_, name):
        for loader in self.loader:
            if loader.has_plugin(type_, name):
                return loader.load_attributes(type_, name)
        return {}

    def load_module(self, type_, name):
        """
        Returns loaded module for plugin

        :param type: plugin type, subfolder of module.plugins
        """
        if (type_, name) in self.modules:
            return self.modules[(type_, name)]
        for loader in self.loader:
            if loader.has_plugin(type_, name):
                try:
                    module = loader.load_module(type_, name)
                    # cache import
                    self.modules[(type_, name)] = module
                    return module
                except Exception as e:
                    self.pyload_core.log.error(
                        self._("Error importing {0}: {1}").format(
                            name, str(e)))
                    # self.pyload_core.print_exc()

    def load_class(self, type_, name):
        """
        Returns the class of a plugin with the same name.
        """
        module = self.load_module(type_, name)
        try:
            if module:
                return getattr(module, name)
        except AttributeError:
            self.pyload_core.log.error(
                self._("Plugin does not define class '{0}'").format(name))

    def find_module(self, fullname):
        # redirecting imports if necessary
        for loader in self.loader:
            if not fullname.startswith(loader.package):
                continue

            # TODO: not well tested
            offset = 1 - loader.package.count(".")

            split = fullname.split(".")
            if len(split) != 4 - offset:
                return None
            type, name = split[2 - offset:4 - offset]

            # check if a different loader than the current one has the plugin
            # in this case import needs redirect
            for l2 in self.loader:
                if l2 is not loader and l2.has_plugin(type, name):
                    return self

        # TODO: Remove when all plugin imports are adapted
        if "module" in fullname:
            return self

    def reload_plugins(self, type_plugins):
        """
        Reloads and reindexes plugins.
        """
        raise NotImplementedError
        # TODO
        # check if reloadable
        # reload
        # save new plugins
        # update index
        # reload accounts

    def is_user_plugin(self, name):
        """
        A plugin suitable for multiple user.
        """
        return any(l.is_user_plugin(name) for l in self.loader)

    def get_category(self, name):
        plugin = self.loader.get_plugin("addon", name)
        if plugin:
            return plugin.category or "addon"

    def load_icon(self, name):
        """
        Load icon for single plugin, base64 encoded.
        """
        raise NotImplementedError

    def check_dependencies(self, type_, name):
        """
        Check deps for given plugin

        :return: List of unfullfilled dependencies
        """
        raise NotImplementedError
