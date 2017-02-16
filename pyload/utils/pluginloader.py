# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals

import io
import os
import re
from builtins import object, range
from collections import defaultdict
from logging import getLogger
from time import time

from pyload.plugin import Base
from pyload.utils.lib.collections import namedtuple
from pyload.utils.lib.eval import const_eval as literal_eval
from pyload.utils.path import makedirs

PluginTuple = namedtuple("PluginTuple", "version re deps category user path")


class BaseAttributes(defaultdict):
    """
    Dictionary that loads defaults values from Base object.
    """

    def __missing__(self, key):
        attr = "__{}__".format(key)
        if not hasattr(Base, attr):
            return defaultdict.__missing__(self, key)

        return getattr(Base, attr)


class LoaderFactory(object):
    """
    Container for multiple plugin loaders.
    """

    def __init__(self, *loader):
        self.loader = list(loader)

    def __iter__(self):
        return self.loader.__iter__()

    def check_versions(self):
        """
        Reduces every plugin loader to the globally newest version.
        Afterwards every plugin is unique across all available loader.
        """
        for type in self.loader[0].iter_types():
            for loader in self.loader:
                # iterate all plugins
                for name, info in loader.get_plugins(type).items():
                    # now iterate all other loaders
                    for l2 in self.loader:
                        if l2 is not loader:
                            l2.remove_plugin(type, name, info.version)

    def find_type(self, name):
        """
        Finds a plugin type for given name.
        """
        for loader in self.loader:
            for t in loader.TYPES:
                if loader.has_plugin(t, name):
                    return t

        return None

    def get_plugin(self, type, name):
        """
        Retrieve a plugin from an available loader.
        """
        for loader in self.loader:
            if loader.has_plugin(type, name):
                return loader.get_plugin(type, name)


class PluginLoader(object):
    """
    Class to provide and load plugins from the file-system.
    """
    TYPES = ("crypter", "hoster", "account", "addon", "network", "internal")

    BUILTIN = re.compile(
        r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(True|False|None|[0-9x.]+)', re.I)
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

        self.create_index()

    def log_debug(self, plugin, name, msg):
        self.log.debug("Plugin {} | {}: {}".format(plugin, name, msg))

    def create_index(self):
        """
        Create information for all plugins available.
        """
        if not os.path.exists(self.path):
            makedirs(self.path)
        if not os.path.exists(os.path.join(self.path, "__init__.py")):
            f = io.open(os.path.join(self.path, "__init__.py"), "wb")
            f.close()

        a = time()
        for type in self.TYPES:
            self.plugins[type] = self.parse(type)

        self.log.debug(
            "Created index of plugins for {} in {:.2f} ms".format(
                self.path, (time() - a) * 1000)
        )

    def parse(self, folder):
        """
        Analyze and parses all plugins in folder.
        """
        plugins = {}
        pfolder = os.path.join(self.path, folder)
        if not os.path.exists(pfolder):
            makedirs(pfolder)
        if not os.path.exists(os.path.join(pfolder, "__init__.py")):
            f = io.open(os.path.join(pfolder, "__init__.py"), "wb")
            f.close()

        for f in os.listdir(pfolder):
            if os.path.isfile(os.path.join(pfolder, f)) and f.endswith(
                    ".py") and not f.startswith("_"):
                # replace suffix and version tag
                name = f[:-3]
                if name[-1] == ".":
                    name = name[:-4]

                plugin = self.parse_plugin(
                    os.path.join(pfolder, f), folder, name)
                if plugin:
                    plugins[name] = plugin

        return plugins

    def parse_attributes(self, filename, name, folder=""):
        """
        Parse attribute dict from plugin.
        """
        with io.open(filename, "rb") as f:
            content = f.read()

        attrs = BaseAttributes()
        for m in self.BUILTIN.findall(
                content) + self.SINGLE.findall(content) + self.parse_multi_line(content):
            # replace gettext function and eval result
            try:
                attrs[m[0]] = literal_eval(m[-1].replace("_(", "("))
            except Exception as e:
                self.log_debug(
                    folder, name, "Error when parsing: {}".format(m[-1]))
                self.log.debug(e.message)

            if not hasattr(Base, "__{}__".format(m[0])):
                # TODO: remove type from all plugins, its not needed
                if m[0] != "type" and m[0] != "author_name":
                    self.log_debug(
                        folder, name, "Unknown attribute '{}'".format(m[0]))

        return attrs

    def parse_multi_line(self, content):
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

            # TODO: strings must be parsed too, otherwise breaks very easily
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

    def parse_plugin(self, filename, folder, name):
        """
        Parses a plugin from disk, folder means plugin type in this context. Also sets config.

        :arg home: dict with plugins, of which the found one will be matched against (according version)
        :returns PluginTuple
        """
        attrs = self.parse_attributes(filename, name, folder)
        if not attrs:
            return

        version = 0
        if "version" in attrs:
            try:
                version = float(attrs['version'])
            except ValueError:
                self.log_debug(
                    folder, name, "Invalid version {}".format(attrs['version']))
                version = 9  # TODO: remove when plugins are fixed, causing update loops
        else:
            self.log_debug(folder, name, "No version attribute")

        if "pattern" in attrs and attrs['pattern']:
            try:
                plugin_re = re.compile(attrs['pattern'], re.I)
            except Exception:
                self.log_debug(
                    folder, name, "Invalid regexp pattern '{}'".format(attrs['pattern']))
                plugin_re = self.NO_MATCH
        else:
            plugin_re = self.NO_MATCH

        deps = attrs['dependencies']
        category = attrs['category'] if folder == "addon" else ""

        # create plugin tuple
        # user_context=True is the default for non addon plugins
        plugin = PluginTuple(version, plugin_re, deps, category,
                             bool(folder != "addon" or attrs['user_context']), filename)

        # These have none or their own config
        if folder in ("internal", "account", "network"):
            return plugin

        if folder == "addon" and "config" not in attrs and not attrs[
                'internal']:
            attrs['config'] = (["activated", "bool", "Activated", False],)

        if "config" in attrs and attrs['config'] is not None:
            config = attrs['config']
            desc = attrs['description']
            expl = attrs['explanation']

            # Convert tuples to list
            config = [list(x) for x in config]

            if folder == "addon" and not attrs['internal']:
                for item in config:
                    if item[0] == "activated":
                        break
                else:  #: activated flag missing
                    config.insert(0, ("activated", "bool", "Activated", False))

            try:
                self.config.add_config_section(name, name, desc, expl, config)
            except Exception:
                self.log_debug(
                    folder, name, "Invalid config  {}".format(config))

        return plugin

    def iter_plugins(self):
        """
        Iterates over all plugins returning (type, name, info)  with info as PluginTuple.
        """
        for type, data in self.plugins.items():
            for name, info in data.items():
                yield type, name, info

    def iter_types(self):
        """
        Iterate over the available plugin types.
        """
        for type in self.plugins.keys():
            yield type

    def has_plugin(self, type, name):
        """
        Check if certain plugin is available.
        """
        return type in self.plugins and name in self.plugins[type]

    def get_plugin(self, type, name):
        """
        Return plugin info for a single entity.
        """
        try:
            return self.plugins[type][name]
        except KeyError:
            return None

    def get_plugins(self, type):
        """
        Return all plugins of given plugin type.
        """
        return self.plugins[type]

    def remove_plugin(self, type, name, version=None):
        """
        Removes a plugin from the index.
        Optionally only when its version is below or equal the available one
        """
        try:
            if version is not None:
                if self.plugins[type][name] <= version:
                    del self.plugins[type][name]
            else:
                del self.plugins[type][name]

        # no errors are thrown if the plugin didn't existed
        except KeyError:
            return

    def is_user_plugin(self, name):
        """
        Determine if given plugin name is enable for user_context in any plugin type.
        """
        for plugins in self.plugins:
            if name in plugins and name[plugins].user:
                return True

        return False

    def save_plugin(self, content):
        """
        Saves a plugin to disk.
        """
        raise NotImplementedError

    def load_module(self, type, name):
        """
        Returns loaded module for plugin

        :param type: plugin type, subfolder of module.plugins
        :raises Exception: Everything could go wrong, failures needs to be catched
        """
        plugins = self.plugins[type]
        # convert path to python recognizable import
        path = os.path.basename(plugins[name].path).replace(
            ".pyc", "").replace(".py", "")
        module = __import__("{}.{}.{}".format(
            self.package, type, path), globals(), locals(), path)
        return module

    def load_attributes(self, type, name):
        """
        Same as `parse_attributes` for already indexed plugins.
        """
        return self.parse_attributes(self.plugins[type][name].path, name, type)
