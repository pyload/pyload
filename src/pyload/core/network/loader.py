# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import ast
import logging
import os
import re
import time
from builtins import object, range, str

from future import standard_library

from pyload.utils.fs import fullpath, lopen, makefile
from pyload.utils.layer.legacy.collections_ import defaultdict, namedtuple

from .base import Base

standard_library.install_aliases()


PluginTuple = namedtuple('PluginTuple', 'version re deps category user path')


class BaseAttributes(defaultdict):
    """
    Dictionary that loads defaults values from Base object.
    """
    def __missing__(self, key):
        attr = "__{0}__".format(key)
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
        for _type in self.loader[0].iter_types():
            for loader in self.loader:
                # iterate all plugins
                for name, info in loader.get_plugins(_type).items():
                    # now iterate all other loaders
                    for l2 in self.loader:
                        if l2 is not loader:
                            l2.remove_plugin(_type, name, info.version)

    def find_type(self, name):
        """
        Finds a plugin type for given name.
        """
        for loader in self.loader:
            for type_ in loader.TYPES:
                if loader.has_plugin(type_, name):
                    return type_

        return None

    def get_plugin(self, type_, name):
        """
        Retrieve a plugin from an available loader.
        """
        for loader in self.loader:
            if loader.has_plugin(type_, name):
                return loader.get_plugin(type_, name)


class PluginLoader(object):
    """
    Class to provide and load plugins from the file-system.
    """
    TYPES = ("crypter", "hoster", "account", "addon", "network", "internal")

    RE_BUILTIN = re.compile(
        r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(True|False|None|[0-9x.]+)',
        flags=re.I)
    RE_SINGLE = re.compile(
        r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(?:r|u|_)?((?:(?<!")"(?!")|\').*(?:(?<!")"(?!")|\'))',
        flags=re.I)
    # finds the beginning of a expression that could span multiple lines
    RE_MULTI = re.compile(
        r'__(?P<attr>[a-z0-9_]+)__\s*=\s*(\(|\{|\[|"{3})', flags=re.I)
    RE_NO_MATCH = re.compile(r'^no_match$')

    # closing symbols
    MULTI_MAP = {
        '{': "}",
        '(': ")",
        '[': "]",
        '"""': '"""'
    }

    def __init__(self, dirname, package, config):
        self.path = fullpath(dirname)
        self.package = package
        self.config = config
        self.log = logging.getLogger()
        self.plugins = {}

        self.create_index()

    def log_debug(self, plugin, name, msg):
        self.log.debug("Plugin {0} | {1}: {2}".format(plugin, name, msg))

    def create_index(self):
        """
        Create information for all plugins available.
        """
        makefile(os.path.join(self.path, "__init__.py"), exist_ok=True)

        a = time.time()
        for _type in self.TYPES:
            self.plugins[_type] = self.parse(_type)

        self.log.debug(
            "Created index of plugins for {0} in {1:.2f} ms".format(
                self.path, (time.time() - a) * 1000)
        )

    def parse(self, folder):
        """
        Analyze and parses all plugins in folder.
        """
        plugins = {}
        pfolder = os.path.join(self.path, folder)
        makefile(os.path.join(pfolder, "__init__.py"), exist_ok=True)

        for fname in os.listdir(pfolder):
            filepath = os.path.join(pfolder, fname)
            if os.path.isfile(filepath) and fname.endswith(
                    ".py") and not fname.startswith("_"):
                # replace suffix and version tag
                name = fname[:-3]
                if name[-1] == ".":
                    name = name[:-4]

                plugin = self.parse_plugin(
                    os.path.join(pfolder, fname), folder, name)
                if plugin:
                    plugins[name] = plugin

        return plugins

    def parse_attributes(self, filename, name, folder=""):
        """
        Parse attribute dict from plugin.
        """
        with lopen(filename, mode='rb') as fp:
            content = fp.read()

        attrs = BaseAttributes()
        for m in self.RE_BUILTIN.findall(
                content) + self.RE_SINGLE.findall(content) + self.parse_multi_line(content):
            # replace gettext function and eval result
            try:
                attrs[m[0]] = ast.literal_eval(
                    m[-1].replace('self._(', '(').replace('_(', '('))
            except Exception as e:
                self.log_debug(
                    folder, name, "Error when parsing: {0}".format(m[-1]))
                self.log.debug(str(e))

            if not hasattr(Base, "__{0}__".format(m[0])):
                # TODO: remove type from all plugins, its not needed
                if m[0] != "type" and m[0] != "author_name":
                    self.log_debug(
                        folder, name, "Unknown attribute '{0}'".format(m[0]))

        return attrs

    def parse_multi_line(self, content):
        # regexp is not enough to parse multi line statements
        attrs = []
        for m in self.RE_MULTI.finditer(content):
            attr = m.group(1)
            char = m.group(2)
            # the end char to search for
            endchar = self.MULTI_MAP[char]
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
            return None

        version = 0
        if "version" in attrs:
            try:
                version = float(attrs['version'])
            except ValueError:
                self.log_debug(
                    folder, name, "Invalid version {0}".format(
                        attrs['version']))
                version = 9  # TODO: remove when plugins are fixed, causing update loops
        else:
            self.log_debug(folder, name, "No version attribute")

        if "pattern" in attrs and attrs['pattern']:
            try:
                re_plugin = re.compile(attrs['pattern'], flags=re.I)
            except Exception:
                self.log_debug(
                    folder, name, "Invalid regexp pattern '{0}'".format(
                        attrs['pattern']))
                re_plugin = self.RE_NO_MATCH
        else:
            re_plugin = self.RE_NO_MATCH

        deps = attrs['dependencies']
        category = attrs['category'] if folder == "addon" else ""

        # create plugin tuple
        # user_context=True is the default for non addon plugins
        plugin = PluginTuple(version, re_plugin, deps, category, bool(
            folder != "addon" or attrs['user_context']), filename)

        # These have none or their own config
        if folder in ("internal", "account", "network"):
            return plugin

        if folder == "addon" and "config" not in attrs and not attrs[
                'internal']:
            attrs['config'] = (["activated", "bool", "Activated", False],)

        # TODO: Rewrite config generator
        if "config" in attrs and attrs['config'] is not None:
            config = attrs['config']
            desc = attrs['description']

            # Convert tuples to list
            config = [list(x) for x in config]

            if folder == "addon" and not attrs['internal']:
                for item in config:
                    if item[0] == "activated":
                        break
                else:  # activated flag missing
                    config.insert(0, ("activated", "bool", "Activated", False))

            try:
                self.config.add_section(name, config, desc=desc)
            except Exception:
                self.log_debug(
                    folder, name, "Invalid config  {0}".format(config))

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
        for _type in self.plugins:
            yield _type

    def has_plugin(self, type_, name):
        """
        Check if certain plugin is available.
        """
        return type_ in self.plugins and name in self.plugins[type_]

    def get_plugin(self, type_, name):
        """
        Return plugin info for a single entity.
        """
        try:
            return self.plugins[type_][name]
        except KeyError:
            return None

    def get_plugins(self, type_):
        """
        Return all plugins of given plugin type.
        """
        return self.plugins[type_]

    def remove_plugin(self, type_, name, version=None):
        """
        Removes a plugin from the index.
        Optionally only when its version is below or equal the available one
        """
        try:
            if version is not None:
                if self.plugins[type_][name] <= version:
                    del self.plugins[type_][name]
            else:
                del self.plugins[type_][name]
        # no errors are thrown if the plugin didn't existed
        except KeyError:
            return None

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

    def load_module(self, type_, name):
        """
        Returns loaded module for plugin

        :param type: plugin type, subfolder of module.plugins
        :raises Exception: Everything could go wrong, failures needs to be catched
        """
        plugins = self.plugins[type_]
        # convert path to python recognizable import
        filename = os.path.basename(plugins[name].path)
        name = filename.replace(".pyc", "").replace(".py", "")
        module = __import__("{0}.{1}.{2}".format(
            self.package, type_, name), globals(), locals(), name)
        return module

    def load_attributes(self, type_, name):
        """
        Same as `parse_attributes` for already indexed plugins.
        """
        return self.parse_attributes(
            self.plugins[type_][name].path, name, type_)
