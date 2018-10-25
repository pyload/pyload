# -*- coding: utf-8 -*-
# @author: mkaay, RaNaN

import importlib
import os
import re
import sys
import traceback
from ast import literal_eval
from builtins import PKGDIR, object, str
from itertools import chain

import semver


class PluginManager(object):
    ROOT = "pyload.plugins."
    USERROOT = "userplugins."
    TYPES = (
        "crypter",
        "container",
        "hoster",
        "captcha",
        "account",
        "addon",
        "internal",
    )

    _PATTERN = re.compile(r'\s*__pattern__\s*=\s*r?(?:"|\')([^"\']+)')
    _VERSION = re.compile(r'\s*__version__\s*=\s*(?:"|\')([\d.]+)')
    _PYLOAD_VERSION = re.compile(r'\s*__pyload_version__\s*=\s*(?:"|\')([\d.]+)')
    _CONFIG = re.compile(r"\s*__config__\s*=\s*(\[[^\]]+\])", re.MULTILINE)
    _DESC = re.compile(r'\s*__description__\s*=\s*(?:"|"""|\')([^"\']+)', re.MULTILINE)

    def __init__(self, core):
        self.pyload = core
        self._ = core._

        self.plugins = {}
        self.createIndex()

        # register for import addon
        sys.meta_path.append(self)

    def createIndex(self):
        """
        create information for all plugins available.
        """

        def merge(dst, src, overwrite=False):
            """
            merge dict of dicts.
            """
            for name in src:
                if name in dst:
                    if overwrite:
                        dst[name].update(src[name])
                    else:
                        for k in set(src[name].keys()) - set(dst[name].keys()):
                            dst[name][k] = src[name][k]
                else:
                    dst[name] = src[name]

        sys.path.append(os.path.join(self.pyload.userdir, "userplugins"))

        userplugins_dir = os.path.join(self.pyload.userdir, "userplugins")
        os.makedirs(userplugins_dir, exist_ok=True)

        try:
            f = open(os.path.join(userplugins_dir, "__init__.py"), mode="wb")
            f.close()
        except Exception:
            pass

        self.crypterPlugins, config = self.parse("crypter", pattern=True)
        self.plugins["crypter"] = self.crypterPlugins
        default_config = config

        self.containerPlugins, config = self.parse("container", pattern=True)
        self.plugins["container"] = self.containerPlugins
        merge(default_config, config)

        self.hosterPlugins, config = self.parse("hoster", pattern=True)
        self.plugins["hoster"] = self.hosterPlugins
        merge(default_config, config)

        self.addonPlugins, config = self.parse("addon")
        self.plugins["addon"] = self.addonPlugins
        merge(default_config, config)

        self.captchaPlugins, config = self.parse("captcha")
        self.plugins["captcha"] = self.captchaPlugins
        merge(default_config, config)

        self.accountPlugins, config = self.parse("account")
        self.plugins["account"] = self.accountPlugins
        merge(default_config, config)

        self.internalPlugins, config = self.parse("internal")
        self.plugins["internal"] = self.internalPlugins
        merge(default_config, config)

        for name, config in default_config.items():
            desc = config.pop("desc", "")
            config = [[k] + list(v) for k, v in config.items()]
            try:
                self.pyload.config.addPluginConfig(name, config, desc)
            except Exception as exc:
                self.pyload.log.error("Invalid config in {}: {}".format(name, config), exc)

        self.pyload.log.debug("created index of plugins")

    def parse(self, folder, pattern=False, home={}):
        """
        returns dict with information
        home contains parsed plugins from pyload.

        {
        name : {path, version, config, (pattern, re), (plugin, class)}
        }

        """
        plugins = {}
        if home:
            pfolder = os.path.join(self.pyload.userdir, "userplugins", folder)
            os.makedirs(pfolder, exist_ok=True)
            try:
                f = open(os.path.join(pfolder, "__init__.py"), mode="wb")
                f.close()
            except Exception:
                pass
        else:
            pfolder = os.path.join(PKGDIR, "plugins", folder)

        configs = {}
        for f in os.listdir(pfolder):
            if (
                os.path.isfile(os.path.join(pfolder, f)) and f.endswith(".py")
            ) and not f.startswith("_"):

                with open(os.path.join(pfolder, f)) as data:
                    content = data.read()

                name = f[:-3]
                if name[-1] == ".":
                    name = name[:-4]

                m_pyver = self._PYLOAD_VERSION.search(content)
                if m_pyver is None:
                    self.pyload.log.debug(
                        "__pyload_version__ not found in plugin {}".format(name)
                    )
                else:
                    pyload_version = m_pyver.group(1)

                    requires_version = "{}.0".format(pyload_version)
                    requires_version_info = semver.parse_version_info(requires_version)

                    if self.pyload.version_info.major:
                        core_version = self.pyload.version_info.major
                        plugin_version = requires_version_info.major
                    else:
                        core_version = self.pyload.version_info.minor
                        plugin_version = requires_version_info.minor

                    if core_version > plugin_version:
                        self.pyload.log.warning(
                            self._(
                                "Plugin {} not compatible with current pyLoad version"
                            ).format(name)
                        )
                        continue

                m_ver = self._VERSION.search(content)
                if m_ver is None:
                    self.pyload.log.debug(
                        "__version__ not found in plugin {}".format(name)
                    )
                    version = 0
                else:
                    version = float(m_ver.group(1))

                # home contains plugins from pyload root
                if isinstance(home, dict) and name in home:
                    if home[name]["v"] >= version:
                        continue

                plugins[name] = {}
                plugins[name]["v"] = version

                module = f.replace(".pyc", "").replace(".py", "")

                # the plugin is loaded from user directory
                plugins[name]["user"] = True if home else False
                plugins[name]["name"] = module

                if pattern:
                    m_pat = self._PATTERN.search(content)
                    pattern = r"^unmachtable$" if m_pat is None else m_pat.group(1)

                    plugins[name]["pattern"] = pattern

                    try:
                        plugins[name]["re"] = re.compile(pattern)
                    except Exception:
                        self.pyload.log.error(
                            self._("{} has a invalid pattern.").format(name)
                        )

                # internals have no config
                if folder == "internal":
                    self.pyload.config.deleteConfig(name)
                    continue

                m_desc = self._DESC.search(content)
                desc = "" if m_desc is None else m_desc.group(1)

                config = self._CONFIG.findall(content)
                if not config:
                    new_config = {"enabled": ["bool", "Activated", False], "desc": desc}
                    configs[name] = new_config
                    continue

                config = literal_eval(
                    config[0].strip().replace("\n", "").replace("\r", "")
                )

                if isinstance(config, list) and all(
                    isinstance(c, tuple) for c in config
                ):
                    config = {x[0]: x[1:] for x in config}
                else:
                    self.pyload.log.error(
                        "Invalid config in {}: {}".format(name, config)
                    )
                    continue

                if folder == "addons" and "enabled" not in config:
                    config["enabled"] = ["bool", "Activated", False]

                config["desc"] = desc
                configs[name] = config

        if not home:
            temp_plugins, temp_configs = self.parse(folder, pattern, plugins or True)
            plugins.update(temp_plugins)
            configs.update(temp_configs)

        return plugins, configs

    def parseUrls(self, urls):
        """
        parse plugins for given list of urls.
        """

        last = None
        res = []  #: tupels of (url, plugin)

        for url in urls:
            if type(url) not in (
                str,
                bytes,
                memoryview,
            ):  #: check memoryview (as py2 byffer)
                continue
            found = False

            if last and last[1]["re"].match(url):
                res.append((url, last[0]))
                continue

            for name, value in chain(
                iter(self.crypterPlugins.items()),
                iter(self.hosterPlugins.items()),
                iter(self.containerPlugins.items()),
            ):
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
        """
        return plugin module from hoster|decrypter|container.
        """
        plugin, type = self.findPlugin(name)

        if not plugin:
            self.pyload.log.warning("Plugin {} not found.".format(name))
            plugin = self.hosterPlugins["BasePlugin"]

        if "new_module" in plugin and not original:
            return plugin["new_module"]

        return self.loadModule(type, name)

    def getPluginName(self, name):
        """
        used to obtain new name if other plugin was injected.
        """
        plugin, type = self.findPlugin(name)

        if "new_name" in plugin:
            return plugin["new_name"]

        return name

    def loadModule(self, type, name):
        """
        Returns loaded module for plugin.

        :param type: plugin type, subfolder of module.plugins
        :param name:
        """
        plugins = self.plugins[type]
        if name in plugins:
            if "pyload" in plugins[name]:
                return plugins[name]["pyload"]
            try:
                module = __import__(
                    self.ROOT + "{}.{}".format(type, plugins[name]["name"]),
                    globals(),
                    locals(),
                    plugins[name]["name"],
                )
                plugins[name]["pyload"] = module  #: cache import, maybe unneeded
                return module
            except Exception as exc:
                self.pyload.log.error(
                    self._("Error importing {name}: {msg}").format(name=name, msg=exc)
                )
                if self.pyload.debug:
                    traceback.print_exc()
        else:
            self.pyload.log.debug("Plugin {} not found".format(name))
            self.pyload.log.debug("Available plugins : {}".format(str(plugins)))

    def loadClass(self, type, name):
        """
        Returns the class of a plugin with the same name.
        """
        module = self.loadModule(type, name)
        if module:
            return getattr(module, name)

    def getAccountPlugins(self):
        """
        return list of account plugin names.
        """
        return list(self.accountPlugins.keys())

    def find_module(self, fullname, path=None):
        # redirecting imports if necesarry
        if fullname.startswith(self.ROOT) or fullname.startswith(
            self.USERROOT
        ):  #: os.seperate pyload plugins
            if fullname.startswith(self.USERROOT):
                user = 1
            else:
                user = 0  #: used as bool and int

            split = fullname.split(".")
            if len(split) != 4 - user:
                return
            type, name = split[2 - user : 4 - user]

            if type in self.plugins and name in self.plugins[type]:
                # userplugin is a newer version
                if not user and self.plugins[type][name]["user"]:
                    return self
                # imported from userdir, but pyloads is newer
                if user and not self.plugins[type][name]["user"]:
                    return self

    def load_module(self, name, replace=True):
        if name not in sys.modules:  #: could be already in modules
            if replace:
                if self.ROOT in name:
                    newname = name.replace(self.ROOT, self.USERROOT)
                else:
                    newname = name.replace(self.USERROOT, self.ROOT)
            else:
                newname = name

            base, plugin = newname.rsplit(".", 1)

            self.pyload.log.debug("Redirected import {} -> {}".format(name, newname))

            module = __import__(newname, globals(), locals(), [plugin])
            # inject under new an old name
            sys.modules[name] = module
            sys.modules[newname] = module

        return sys.modules[name]

    def reloadPlugins(self, type_plugins):
        """
        reloads and reindexes plugins.
        """

        def merge(dst, src, overwrite=False):
            """
            merge dict of dicts.
            """
            for name in src:
                if name in dst:
                    if overwrite:
                        dst[name].update(src[name])
                    else:
                        for k in set(src[name].keys()) - set(dst[name].keys()):
                            dst[name][k] = src[name][k]
                else:
                    dst[name] = src[name]

        if not type_plugins:
            return False

        self.pyload.log.debug("Request reload of plugins: {}".format(type_plugins))

        as_dict = {}
        for t, n in type_plugins:
            if t in as_dict:
                as_dict[t].append(n)
            else:
                as_dict[t] = [n]

        # we do not reload addons or internals, would cause to much side effects
        if "addons" in as_dict or "internal" in as_dict:
            return False

        for type in as_dict.keys():
            for plugin in as_dict[type]:
                if plugin in self.plugins[type]:
                    if "pyload" in self.plugins[type][plugin]:
                        self.pyload.log.debug("Reloading {}".format(plugin))
                        importlib.reload(self.plugins[type][plugin]["pyload"])

        # index creation
        self.crypterPlugins, config = self.parse("crypter", pattern=True)
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
            desc = config.pop("desc", "")
            config = [[k] + list(v) for k, v in config.items()]
            try:
                self.pyload.config.addPluginConfig(name, config, desc)
            except Exception:
                self.pyload.log.error("Invalid config in {}: {}".format(name, config))

        if "account" in as_dict:  #: accounts needs to be reloaded
            self.pyload.accountManager.initPlugins()
            self.pyload.scheduler.addJob(0, self.pyload.accountManager.getAccountInfos)

        return True
