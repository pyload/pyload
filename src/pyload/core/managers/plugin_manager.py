# -*- coding: utf-8 -*-

import importlib
import os
import re
import sys
from ast import literal_eval
from importlib.abc import MetaPathFinder
from itertools import chain

# import semver

from pyload import APPID, PKGDIR


class ImportRedirector(MetaPathFinder):
    ROOT = "pyload.plugins."
    USERROOT = "plugins."

    def __init__(self, core):
        self.pyload = core
        self._ = core._

        userplugins_dir = os.path.join(self.pyload.userdir, *self.USERROOT.split("."))
        os.makedirs(userplugins_dir, exist_ok=True)
        try:
            with open(os.path.join(userplugins_dir, "__init__.py"), mode="wb"):
                pass
        except OSError:
            pass

        # add USERROOT to sys.path
        sys.path.append(self.pyload.userdir)

        # register for import addon
        sys.meta_path.append(self)

    def find_module(self, fullname, path=None):
        # redirecting imports if necessary
        if fullname.startswith(self.ROOT) or fullname.startswith(
            self.USERROOT
        ):  #: separate pyload plugins
            if fullname.startswith(self.USERROOT):
                user = 1
            else:
                user = 0  #: used as bool and int

            split = fullname.split(".")
            if len(split) == 3 - user:
                return self
            elif len(split) == 4 - user:
                plugin_type, plugin_name = split[2 - user: 4 - user]
                if plugin_type != "base" and plugin_type[-1] == "s":
                    plugin_type = plugin_type[:-1]  #: remove trailing plural "s" character

                plugins = self.pyload.plugin_manager.plugins
                if plugin_type in plugins and plugin_name in plugins[plugin_type]:
                    # userplugin is a newer version
                    if not user and plugins[plugin_type][plugin_name]["user"]:
                        return self
                    # imported from userplugins dir, but pyLoad's version is newer
                    if user and not plugins[plugin_type][plugin_name]["user"]:
                        return self

        return None

    def load_module(self, fullname, replace=True):
        if fullname not in sys.modules:  #: could be already in modules
            if replace:
                if self.ROOT in fullname:
                    newname = fullname.replace(self.ROOT, self.USERROOT)

                else:
                    newname = fullname.replace(self.USERROOT, self.ROOT)

            else:
                newname = fullname

            base, plugin = newname.rsplit(".", 1)

            self.pyload.log.debug("Redirected import {} -> {}".format(fullname, newname))

            module = __import__(newname, globals(), locals(), [plugin])

            #: Inject under new and old name
            sys.modules[fullname] = module
            sys.modules[newname] = module

        return sys.modules[fullname]


class PluginManager:
    TYPES = (
        "decrypter",
        "container",
        "downloader",
        "anticaptcha",
        "extractor",
        "account",
        "addon",
        "base",
    )

    _RE_PATTERN = re.compile(r'\s*__pattern__\s*=\s*r?["\']([^"\']+)')
    _RE_VERSION = re.compile(r'\s*__version__\s*=\s*["\']([\d.]+)')
    # _RE_PYLOAD_VERSION = re.compile(r'\s*__pyload_version__\s*=\s*(?:"|\')([\d.]+)')
    _RE_CONFIG = re.compile(r"\s*__config__\s*=\s*(\[[^\]]+\])", re.MULTILINE)
    _RE_DESC = re.compile(r'\s*__description__\s*=\s*(?:"|"""|\')([^"\']+)', re.MULTILINE)

    def __init__(self, core):
        self.pyload = core
        self._ = core._

        self.plugins = {}
        self.account_plugins = []
        self.addon_plugins = []
        self.anticaptcha_plugins = []
        self.container_plugins = []
        self.decrypter_plugins = []
        self.downloader_plugins = []
        self.extractor_plugins = []
        self.base_plugins = []

        self.import_redirector = ImportRedirector(core)

        self.create_index()

        # save generated config
        self.pyload.config.save_config(self.pyload.config.plugin, self.pyload.config.pluginpath)

    def create_index(self):
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

        self.pyload.log.debug("Indexing plugins...")

        self.decrypter_plugins, config = self.parse("decrypters", pattern=True)
        self.plugins["decrypter"] = self.decrypter_plugins
        default_config = config

        self.container_plugins, config = self.parse("containers", pattern=True)
        self.plugins["container"] = self.container_plugins
        merge(default_config, config)

        self.downloader_plugins, config = self.parse("downloaders", pattern=True)
        self.plugins["downloader"] = self.downloader_plugins
        merge(default_config, config)

        self.addon_plugins, config = self.parse("addons")
        self.plugins["addon"] = self.addon_plugins
        merge(default_config, config)

        self.anticaptcha_plugins, config = self.parse("anticaptchas")
        self.plugins["anticaptcha"] = self.anticaptcha_plugins
        merge(default_config, config)

        self.extractor_plugins, config = self.parse("extractors")
        self.plugins["extractor"] = self.extractor_plugins
        merge(default_config, config)

        self.account_plugins, config = self.parse("accounts")
        self.plugins["account"] = self.account_plugins
        merge(default_config, config)

        self.base_plugins, config = self.parse("base")
        self.plugins["base"] = self.base_plugins
        merge(default_config, config)

        for name, config in default_config.items():
            desc = config.pop("desc", "")
            config = [[k] + list(v) for k, v in config.items()]
            try:
                self.pyload.config.add_plugin_config(name, config, desc)
            except Exception:
                self.pyload.log.error(
                    self._("Invalid config in {}: {}").format(name, config),
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )

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
            pfolder = os.path.join(self.pyload.userdir, "plugins", folder)
            os.makedirs(pfolder, exist_ok=True)
            try:
                fp = open(os.path.join(pfolder, "__init__.py"), mode="wb")
                fp.close()
            except Exception:
                pass
        else:
            pfolder = os.path.join(PKGDIR, "plugins", folder)

        configs = {}
        for entry in os.listdir(pfolder):
            if (
                os.path.isfile(os.path.join(pfolder, entry)) and entry.endswith(".py")
            ) and not entry.startswith("_"):

                with open(os.path.join(pfolder, entry), encoding="utf-8-sig") as data:
                    content = data.read()

                name = entry[:-3] #: Trim ending ".py"

                # m_pyver = self._RE_PYLOAD_VERSION.search(content)
                # if m_pyver is None:
                #     self.pyload.log.debug(
                #         f"__pyload_version__ not found in plugin {name}"
                #     )
                # else:
                #     pyload_version = m_pyver.group(1)

                #     requires_version = f"{pyload_version}.0"
                #     requires_version_info = semver.parse_version_info(requires_version)

                #     if self.pyload.version_info.major:
                #         core_version = self.pyload.version_info.major
                #         plugin_version = requires_version_info.major
                #     else:
                #         core_version = self.pyload.version_info.minor
                #         plugin_version = requires_version_info.minor

                #     if core_version > plugin_version:
                #         self.pyload.log.warning(
                #             self._(
                #                 "Plugin {} not compatible with current pyLoad version"
                #             ).format(name)
                #         )
                #         continue

                m_ver = self._RE_VERSION.search(content)
                if m_ver is None:
                    self.pyload.log.debug(f"__version__ not found in plugin {name}")
                    version = 0
                else:
                    version = float(m_ver.group(1))

                # home contains plugins from pyload root
                if isinstance(home, dict) and name in home:
                    if home[name]["v"] >= version:
                        continue

                plugins[name] = {}
                plugins[name]["v"] = version

                # was the plugin is loaded from user directory?
                plugins[name]["user"] = True if home else False
                plugins[name]["name"] = name
                plugins[name]["folder"] = folder

                if pattern:
                    m_pat = self._RE_PATTERN.search(content)
                    pattern = r"^unmachtable$" if m_pat is None else m_pat.group(1)

                    plugins[name]["pattern"] = pattern

                    try:
                        plugins[name]["re"] = re.compile(pattern)
                    except re.error:
                        plugins[name]["re"] = re.compile(r"(?!.*)")
                        self.pyload.log.error(
                            self._("{} has a invalid pattern").format(name)
                        )

                # internals have no config
                if folder == "base":
                    self.pyload.config.delete_config(name)
                    continue

                m_desc = self._RE_DESC.search(content)
                desc = "" if m_desc is None else m_desc.group(1)

                config = self._RE_CONFIG.findall(content)
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
                        self._("Invalid config in {}: {}").format(name, config)
                    )
                    continue

                if folder == "addons" and "enabled" not in config:
                    config["enabled"] = ["bool", "Activated", False]

                config["desc"] = desc
                configs[name] = config

        if not home and folder != "base":
            temp_plugins, temp_configs = self.parse(folder, pattern, plugins or True)
            plugins.update(temp_plugins)
            configs.update(temp_configs)

        return plugins, configs

    def parse_urls(self, urls):
        """
        parse plugins for given list of urls.
        """
        last = (None, {})
        res = []  #: tuples of (url, plugin)

        for url in urls:
            if type(url) not in (
                str,
                bytes,
                memoryview,
            ):  #: check memoryview (as py2 buffer)
                continue
            found = False

            # NOTE: E1136: Value 'last' is unsubscriptable (unsubscriptable-object)
            if last != (None, {}) and last[1]["re"].match(url):
                res.append((url, last[0]))
                continue

            for name, value in chain(
                self.decrypter_plugins.items(),
                self.downloader_plugins.items(),
                self.container_plugins.items(),
            ):
                if value["re"].match(url):
                    res.append((url, name))
                    last = (name, value)
                    found = True
                    break

            if not found:
                res.append((url, "DefaultPlugin"))

        return res

    def find_plugin(self, name, pluginlist=("decrypter", "downloader", "container")):
        for ptype in pluginlist:
            if name in self.plugins[ptype]:
                return self.plugins[ptype][name], ptype
        return None, None

    def get_plugin(self, name, original=False):
        """
        return plugin module from downloader|decrypter|container.
        """
        plugin, type = self.find_plugin(name)

        if not plugin:
            self.pyload.log.warning(self._("Plugin {} not found").format(name))
            plugin = self.downloader_plugins["DefaultPlugin"]

        if "new_module" in plugin and not original:
            return plugin["new_module"]

        return self.load_module(type, name)

    def get_plugin_name(self, name):
        """
        used to obtain new name if other plugin was injected.
        """
        plugin, type = self.find_plugin(name)

        if "new_name" in plugin:
            return plugin["new_name"]

        return name

    def load_module(self, module_type, module_name):
        """
        Returns loaded module for plugin.

        :param module_type: plugin type, subfolder of pyload.plugins
        :param module_name: plugin name
        """
        plugins = self.plugins[module_type]
        if module_name in plugins:
            if APPID in plugins[module_name]:
                return plugins[module_name][APPID]
            try:
                module_name = plugins[module_name]["name"]
                module_folder = plugins[module_name]["folder"]
                module = __import__(
                    self.import_redirector.ROOT + f"{module_folder}.{module_name}",
                    globals(),
                    locals(),
                    plugins[module_name]["name"],
                )
                plugins[module_name][APPID] = module  #: cache import, maybe unneeded
                return module
            except Exception as exc:
                self.pyload.log.error(
                    self._("Error importing {name}: {msg}").format(name=module_name, msg=exc),
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )
        else:
            self.pyload.log.debug(f"Plugin {module_name} not found")
            self.pyload.log.debug(f"Available plugins : {plugins}")

    def load_class(self, type, name):
        """
        Returns the class of a plugin with the same name.
        """
        module = self.load_module(type, name)
        if module:
            return getattr(module, name)

    def get_account_plugins(self):
        """
        return list of account plugin names.
        """
        return list(self.account_plugins.keys())

    def reload_plugins(self, type_plugins):
        """
        reloads and reindex plugins.
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

        self.pyload.log.debug(f"Request reload of plugins: {type_plugins}")

        as_dict = {}
        for t, n in type_plugins:
            if t in as_dict:
                as_dict[t].append(n)
            else:
                as_dict[t] = [n]

        # we do not reload addons or base, would cause too much side effects
        if "addon" in as_dict or "base" in as_dict:
            return False

        for plugin_type in as_dict.keys():
            for plugin_name in as_dict[plugin_type]:
                if plugin_name in self.plugins[plugin_type]:
                    if APPID in self.plugins[plugin_type][plugin_name]:
                        self.pyload.log.debug(f"Reloading {plugin_name}")
                        importlib.reload(self.plugins[plugin_type][plugin_name][APPID])

        # index creation
        self.decrypter_plugins, config = self.parse("decrypters", pattern=True)
        self.plugins["decrypter"] = self.decrypter_plugins
        default_config = config

        self.container_plugins, config = self.parse("containers", pattern=True)
        self.plugins["container"] = self.container_plugins
        merge(default_config, config)

        self.downloader_plugins, config = self.parse("downloaders", pattern=True)
        self.plugins["downloader"] = self.downloader_plugins
        merge(default_config, config)

        temp, config = self.parse("addons")
        merge(default_config, config)

        self.anticaptcha_plugins, config = self.parse("anticaptchas")
        self.plugins["anticaptcha"] = self.anticaptcha_plugins
        merge(default_config, config)

        self.extractor_plugins, config = self.parse("extractors")
        self.plugins["extractor"] = self.extractor_plugins
        merge(default_config, config)

        self.account_plugins, config = self.parse("accounts")
        self.plugins["account"] = self.account_plugins
        merge(default_config, config)

        for name, config in default_config.items():
            desc = config.pop("desc", "")
            config = [[k] + list(v) for k, v in config.items()]
            try:
                self.pyload.config.add_plugin_config(name, config, desc)
            except Exception:
                self.pyload.log.error(
                    self._("Invalid config in {}: {}").format(name, config),
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )

        if "account" in as_dict:  #: accounts needs to be reloaded
            self.pyload.account_manager.init_plugins()
            self.pyload.scheduler.add_job(
                0, self.pyload.account_manager.get_account_infos
            )

        return True
