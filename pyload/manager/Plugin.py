# -*- coding: utf-8 -*-

from __future__ import with_statement

import re
import sys

from itertools import chain
from os import listdir, makedirs
from os.path import isdir, isfile, join, exists, abspath
from sys import version_info
from traceback import print_exc
from urllib import unquote

from SafeEval import const_eval as literal_eval


class PluginManager(object):
    ROOT     = "pyload.plugin."
    USERROOT = "userplugins."
    TYPES    = ["account", "addon", "container", "crypter", "extractor", "hook", "hoster", "internal", "ocr"]

    PATTERN = re.compile(r'__pattern\s*=\s*u?r("|\')([^"\']+)')
    VERSION = re.compile(r'__version\s*=\s*("|\')([\d.]+)')
    CONFIG  = re.compile(r'__config\s*=\s*\[([^\]]+)', re.M)
    DESC    = re.compile(r'__description\s*=\s*("|"""|\')([^"\']+)')

    def __init__(self, core):
        self.core = core

        self.plugins = {}
        self.createIndex()

        # register for import addon
        sys.meta_path.append(self)

    def loadTypes(self):
        rootdir = join(pypath, "pyload", "plugin")
        userdir = "userplugins"

        types = set().union(*[[d for d in listdir(p) if isdir(join(p, d))]
                              for p in (rootdir, userdir) if exists(p)])

        if not types:
            self.core.log.critical(_("No plugins found!"))

        self.TYPES = list(set(self.TYPES) | types)

    def createIndex(self):
        """create information for all plugins available"""

        sys.path.append(abspath(""))

        self.loadTypes()

        configs = []

        for type in self.TYPES:
            self.plugins[type] = self.parse(type)
            setattr(self, "%sPlugins" % type, self.plugins[type])
            configs.extend("%s_%s" % (p, type) for p in self.plugins[type])

        self.core.config.removeDeletedPlugins(configs)

        self.core.log.debug("Created index of plugins")

    def parse(self, folder, rootplugins={}):
        """
        returns dict with information
        home contains parsed plugins from pyload.
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
                self.core.log.critical(str(e))
                return rootplugins

        else:
            pfolder = join(pypath, "pyload", "plugin", folder)

        for f in listdir(pfolder):
            if isfile(join(pfolder, f)) and f.endswith(".py") and not f.startswith("_"):

                try:
                    with open(join(pfolder, f)) as data:
                        content = data.read()

                except IOError, e:
                    self.core.log.error(str(e))
                    continue

                name = f[:-3]
                if name[-1] == ".":
                    name = name[:-4]

                version = self.VERSION.findall(content)
                if version:
                    version = float(version[0][1])
                else:
                    version = 0

                if rootplugins and name in rootplugins:
                    if rootplugins[name]['version'] >= version:
                        continue

                plugins[name] = {}
                plugins[name]['version'] = version

                module = f.replace(".pyc", "").replace(".py", "")

                # the plugin is loaded from user directory
                plugins[name]['user'] = True if rootplugins else False
                plugins[name]['name'] = module

                pattern = self.PATTERN.findall(content)

                if pattern:
                    pattern = pattern[0][1]

                    try:
                        regexp = re.compile(pattern)
                    except Exception:
                        self.core.log.error(_("%s has a invalid pattern") % name)
                        pattern = r'^unmatchable$'
                        regexp = re.compile(pattern)

                    plugins[name]['pattern'] = pattern
                    plugins[name]['re'] = regexp

                # internals have no config
                if folder == "internal":
                    self.core.config.deleteConfig("internal")
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

                        if folder not in ("account", "internal") and not [True for item in config if item[0] == "activated"]:
                            config.insert(0, ["activated", "bool", "Activated", False if folder in ("addon", "hook") else True])

                        self.core.config.addPluginConfig("%s_%s" % (name, folder), config, desc)
                    except Exception:
                        self.core.log.error("Invalid config in %s: %s" % (name, config))

                elif folder in ("addon", "hook"):  # force config creation
                    desc = self.DESC.findall(content)
                    desc = desc[0][1] if desc else ""
                    config = (["activated", "bool", "Activated", False],)

                    try:
                        self.core.config.addPluginConfig("%s_%s" % (name, folder), config, desc)
                    except Exception:
                        self.core.log.error("Invalid config in %s: %s" % (name, config))

        if not rootplugins and plugins:  #: Double check
            plugins.update(self.parse(folder, plugins))

        return plugins

    def parseUrls(self, urls):
        """parse plugins for given list of urls"""

        last = None
        res  = []  #: tupels of (url, plugintype, pluginname)

        for url in urls:
            if type(url) not in (str, unicode, buffer):
                continue

            url = unquote(url)

            if last and last[2]['re'].match(url):
                res.append((url, last[0], last[1]))
                continue

            for plugintype in self.TYPES:
                m = None
                for name, plugin in self.plugins[plugintype].iteritems():
                    try:
                        if 'pattern' in plugin:
                            m = plugin['re'].match(url)

                    except KeyError:
                        self.core.log.error(_("Plugin [%(type)s] %(name)s skipped due broken pattern")
                                            % {'name': plugin['name'], 'type': plugintype})

                    if m:
                        res.append((url, plugintype, name))
                        last = (plugintype, name, plugin)
                        break
                if m:
                    break
            else:
                res.append((url, "internal", "BasePlugin"))
        print res
        return res

    def findPlugin(self, type, name):
        if type not in self.plugins:
            return None

        elif name not in self.plugins[type]:
            self.core.log.warning(_("Plugin [%(type)s] %(name)s not found | Using plugin: [internal] BasePlugin")
                                  % {'name': name, 'type': type})
            return self.internalPlugins["BasePlugin"]

        else:
            return self.plugins[type][name]

    def getPlugin(self, type, name, original=False):
        """return plugin module from hoster|decrypter|container"""
        plugin = self.findPlugin(type, name)

        if plugin is None:
            return {}

        if "new_module" in plugin and not original:
            return plugin['new_module']
        else:
            return self.loadModule(type, name)

    def getPluginName(self, type, name):
        """ used to obtain new name if other plugin was injected"""
        plugin = self.findPlugin(type, name)

        if plugin is None:
            return ""

        if "new_name" in plugin:
            return plugin['new_name']

        return name

    def loadModule(self, type, name):
        """ Returns loaded module for plugin

        :param type: plugin type, subfolder of pyload.plugins
        :param name:
        """
        plugins = self.plugins[type]

        if name in plugins:
            if "module" in plugins[name]:
                return plugins[name]['module']

            try:
                module = __import__(self.ROOT + "%s.%s" % (type, plugins[name]['name']), globals(), locals(),
                                    plugins[name]['name'])

            except Exception, e:
                self.core.log.error(_("Error importing plugin: [%(type)s] %(name)s (v%(version).2f) | %(errmsg)s")
                                    % {'name': name, 'type': type, 'version': plugins[name]['version'], "errmsg": str(e)})
                if self.core.debug:
                    print_exc()

            else:
                plugins[name]['module'] = module  # : cache import, maybe unneeded

                self.core.log.debug(_("Loaded plugin: [%(type)s] %(name)s (v%(version).2f)")
                                    % {'name': name, 'type': type, 'version': plugins[name]['version']})
                return module

    def loadClass(self, type, name):
        """Returns the class of a plugin with the same name"""
        module = self.loadModule(type, name)
        if module:
            return getattr(module, name)
        else:
            return None

    def getAccountPlugins(self):
        """return list of account plugin names"""
        return self.accountPlugins.keys()

    def find_module(self, fullname, path=None):
        # redirecting imports if necesarry
        if fullname.startswith(self.ROOT) or fullname.startswith(self.USERROOT):  # seperate pyload plugins
            if fullname.startswith(self.USERROOT): user = 1
            else: user = 0  # used as bool and int

            split = fullname.split(".")
            if len(split) != 4 - user: return
            type, name = split[2 - user:4 - user]

            if type in self.plugins and name in self.plugins[type]:
                # userplugin is a newer version
                if not user and self.plugins[type][name]['user']:
                    return self
                # imported from userdir, but pyloads is newer
                if user and not self.plugins[type][name]['user']:
                    return self

    def load_module(self, name, replace=True):
        if name not in sys.modules:  # could be already in modules
            if replace:
                if self.ROOT in name:
                    newname = name.replace(self.ROOT, self.USERROOT)
                else:
                    newname = name.replace(self.USERROOT, self.ROOT)
            else:
                newname = name

            base, plugin = newname.rsplit(".", 1)

            self.core.log.debug("Redirected import %s -> %s" % (name, newname))

            module = __import__(newname, globals(), locals(), [plugin])
            # inject under new an old name
            sys.modules[name] = module
            sys.modules[newname] = module

        return sys.modules[name]

    def reloadPlugins(self, type_plugins):
        """ reload and reindex plugins """
        if not type_plugins:
            return None

        self.core.log.debug("Request reload of plugins: %s" % type_plugins)

        reloaded = []

        as_dict = {}
        for t, n in type_plugins:
            if t in as_dict:
                as_dict[t].append(n)
            else:
                as_dict[t] = [n]

        for type in as_dict.iterkeys():
            if type in ("addon", "internal"):  # : do not reload them because would cause to much side effects
                self.core.log.debug("Skipping reload for plugin: [%(type)s] %(name)s" % {'name': plugin, 'type': type})
                continue

            for plugin in as_dict[type]:
                if plugin in self.plugins[type] and "module" in self.plugins[type][plugin]:
                    self.core.log.debug(_("Reloading plugin: [%(type)s] %(name)s") % {'name': plugin, 'type': type})

                    try:
                        reload(self.plugins[type][plugin]['module'])

                    except Exception, e:
                        self.core.log.error(_("Error when reloading plugin: [%(type)s] %(name)s") % {'name': plugin, 'type': type}, e)
                        continue

                    else:
                        reloaded.append((type, plugin))

            # index creation
            self.plugins[type] = self.parse(type)
            setattr(self, "%sPlugins" % type, self.plugins[type])

        if "account" in as_dict:  #: accounts needs to be reloaded
            self.core.accountManager.initPlugins()
            self.core.scheduler.addJob(0, self.core.accountManager.getAccountInfos)

        return reloaded  #: return a list of the plugins successfully reloaded

    def reloadPlugin(self, type_plugin):
        """ reload and reindex ONE plugin """
        return True if self.reloadPlugins(type_plugin) else False
