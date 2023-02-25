# -*- coding: utf-8 -*-

import re
import time
from datetime import timedelta

from pyload.core.utils.purge import chars as remove_chars
from pyload.core.utils.purge import uniquify

from .account import BaseAccount


class MultiAccount(BaseAccount):
    __name__ = "MultiAccount"
    __type__ = "account"
    __version__ = "0.24"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Multi-downloader account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    DOMAIN_REPLACEMENTS = [
        (r"ddl\.to", "ddownload.com"),
        (r"180upload\.com", "hundredeightyupload.com"),
        (r"bayfiles\.net", "bayfiles.com"),
        (r"cloudnator\.com", "shragle.com"),
        (r"dfiles\.eu", "depositfiles.com"),
        (r"easy-share\.com", "crocko.com"),
        (r"freakshare\.net", "freakshare.com"),
        (r"hellshare\.com", "hellshare.cz"),
        (r"ifile\.it", "filecloud.io"),
        (r"nowdownload\.\w+", "nowdownload.sx"),
        (r"nowvideo\.\w+", "nowvideo.sx"),
        (r"putlocker\.com", "firedrive.com"),
        (r"share-?rapid\.cz", "multishare.cz"),
        (r"ul\.to", "uploaded.to"),
        (r"uploaded\.net", "uploaded.to"),
        (r"uploadhero\.co", "uploadhero.com"),
        (r"zshares\.net", "zshare.net"),
        (r"^1", "one"),
        (r"^2", "two"),
        (r"^3", "three"),
        (r"^4", "four"),
        (r"^5", "five"),
        (r"^6", "six"),
        (r"^7", "seven"),
        (r"^8", "eight"),
        (r"^9", "nine"),
        (r"^0", "zero"),
    ]

    def init(self):
        self.need_reactivate = False

        self.plugins = []
        self.supported = []

        self.pluginclass = None
        self.pluginmodule = None
        self.plugintype = None

        self.fail_count = 0

        self.init_plugin()

    def init_plugin(self):
        plugin, self.plugintype = self.pyload.plugin_manager.find_plugin(self.classname)

        if plugin:
            self.pluginmodule = self.pyload.plugin_manager.load_module(
                self.plugintype, self.classname
            )
            self.pluginclass = self.pyload.plugin_manager.load_class(
                self.plugintype, self.classname
            )

            self.pyload.addon_manager.add_event("plugin_updated", self.plugins_updated)

            self.periodical.start(3, threaded=True)

        else:
            self.log_warning(
                self._(
                    "Multi-downloader feature will be deactivated due missing plugin reference"
                )
            )

    def plugins_updated(self, type_plugins):
        if not any(
            t in ("base", "addon") for t, n in type_plugins
        ):  #: do nothing if restart required
            self.reactivate()

    def periodical_task(self):
        self.reactivate(refresh=True)

    def replace_domains(self, list):
        for r in self.DOMAIN_REPLACEMENTS:
            pattern, repl = r
            _re = re.compile(pattern, re.I | re.U)
            list = [
                _re.sub(repl, domain) if _re.match(domain) else domain
                for domain in list
            ]

        return list

    def parse_domains(self, list):
        _re = re.compile(
            r"^(?:https?://)?(?:www\.)?(?:\w+\.)*((?:(?:\d{1,3}\.){3}\d{1,3}|[\w\-^_]{3,63}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)",
            re.I | re.U,
        )

        domains = [
            domain.strip().lower()
            for url in list
            for domain in _re.findall(url)
        ]

        return self.replace_domains(uniquify(domains))

    def _grab_hosters(self):
        self.info["data"]["hosters"] = []
        try:
            hosterlist = self.grab_hosters(
                self.user, self.info["login"]["password"], self.info["data"]
            )

            if hosterlist and isinstance(hosterlist, list):
                domains = self.parse_domains(hosterlist)
                self.info["data"]["hosters"] = sorted(domains)
                self.sync(reverse=True)

        except Exception as exc:
            self.log_warning(
                self._("Error loading downloader list for user `{}`").format(self.user),
                exc,
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )

        finally:
            self.log_debug(
                "Downloader list for user `{}`: {}".format(
                    self.user, self.info["data"]["hosters"]
                )
            )
            return self.info["data"]["hosters"]

    def grab_hosters(self, user, password, data):
        """
        Load list of supported downloaders.

        :return: List of domain names
        """
        raise NotImplementedError

    def _override(self):
        prev_supported = self.supported
        new_supported = []
        excluded = []
        self.supported = []

        if self.plugintype == "downloader":
            plugin_map = {
                name.lower(): name
                for name in self.pyload.plugin_manager.downloader_plugins.keys()
            }

            account_list = [
                account.type.lower()
                for account in self.pyload.api.get_accounts(False)
                if account.valid and account.premium
            ]

        else:
            plugin_map = {}
            account_list = [
                name[::-1].replace("Folder"[::-1], "", 1).lower()[::-1]
                for name in self.pyload.plugin_manager.decrypter_plugins.keys()
            ]

        for plugin in self.get_plugins():
            name = remove_chars(plugin, "-.")

            if name in account_list:
                excluded.append(plugin)

            else:
                if name in plugin_map:
                    self.supported.append(plugin_map[name])

                else:
                    new_supported.append(plugin)

        removed = [plugin for plugin in prev_supported if plugin not in self.supported]
        if removed:
            self.log_debug(f"Unload: {', '.join(removed)}")
            for plugin in removed:
                self.unload_plugin(plugin)

        if not self.supported and not new_supported:
            self.log_error(self._("No {} loaded").format(self.plugintype))
            return

        #: Inject plugin plugin
        self.log_debug(
            "Overwritten {}s: {}".format(
                self.plugintype, ", ".join(sorted(self.supported))
            )
        )

        for plugin in self.supported:
            hdict = self.pyload.plugin_manager.plugins[self.plugintype][plugin]
            hdict["new_module"] = self.pluginmodule
            hdict["new_name"] = self.classname

        if excluded:
            self.log_info(
                self._("{}s not overwritten: {}").format(
                    self.plugintype.capitalize(), ", ".join(sorted(excluded))
                )
            )

        if new_supported:
            plugins = sorted(new_supported)

            self.log_debug(f"New {self.plugintype}s: {', '.join(plugins)}")

            #: Create new regexp
            domains = "|".join(x.replace(".", r"\.") for x in plugins)
            pattern = rf".*(?P<DOMAIN>{domains}).*"

            if (
                hasattr(self.pluginclass, "__pattern__")
                and isinstance(self.pluginclass.__pattern__, str)
                and "://" in self.pluginclass.__pattern__
            ):
                pattern = rf"{self.pluginclass.__pattern__}|{pattern}"

            self.log_debug(f"Pattern: {pattern}")

            hdict = self.pyload.plugin_manager.plugins[self.plugintype][self.classname]
            hdict["pattern"] = pattern
            hdict["re"] = re.compile(pattern)

    def get_plugins(self, cached=True):
        if cached and self.plugins:
            return self.plugins

        for _ in range(5):
            try:
                plugin_set = set(self._grab_hosters())
                break

            except Exception as exc:
                self.log_warning(
                    exc,
                    self._("Waiting 1 minute and retry"),
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )
                time.sleep(60)

        else:
            self.log_warning(self._("No hoster list retrieved"))
            return []

        try:
            mh_mode = self.config.get("mh_mode", "all")
            if mh_mode in ("listed", "unlisted"):
                mh_list = (
                    self.config.get("mh_list", "")
                    .replace("|", ",")
                    .replace(";", ",")
                    .split(",")
                )
                config_set = set(mh_list)

                if mh_mode == "listed":
                    plugin_set &= config_set

                else:
                    plugin_set -= config_set

        except Exception as exc:
            self.log_error(exc)

        self.plugins = list(plugin_set)

        return self.plugins

    def unload_plugin(self, plugin):
        #: Reset module
        hdict = self.pyload.plugin_manager.plugins[self.plugintype][plugin]
        if "pyload" in hdict:
            hdict.pop("pyload", None)

        if "new_module" in hdict:
            hdict.pop("new_module", None)
            hdict.pop("new_name", None)

    def reactivate(self, refresh=False):
        reloading = self.info["data"].get("hosters") is not None

        if self.info['login']['valid'] is None:
            return

        else:
            interval = self.config.get('mh_interval', 12) * 60 * 60
            self.periodical.set_interval(interval)

        if self.info['login']['valid'] is False:
            self.fail_count += 1
            if self.fail_count < 3:
                if reloading:
                    self.log_error(
                        self._(
                            "Could not reload hoster list - invalid account, retry in 5 minutes"
                        )
                    )

                else:
                    self.log_error(
                        self._(
                            "Could not load hoster list - invalid account, retry in 5 minutes"
                        )
                    )

                self.periodical.set_interval(timedelta(minutes=5).total_seconds())

            else:
                if reloading:
                    self.log_error(
                        self._(
                            "Could not reload hoster list - invalid account, deactivating"
                        )
                    )

                else:
                    self.log_error(
                        self._(
                            "Could not load hoster list - invalid account, deactivating"
                        )
                    )

                self.deactivate()

            return

        if not self.logged:
            if not self.relogin():
                self.fail_count += 1
                if self.fail_count < 3:
                    if reloading:
                        self.log_error(
                            self._(
                                "Could not reload hoster list - login failed, retry in 5 minutes"
                            )
                        )

                    else:
                        self.log_error(
                            self._(
                                "Could not load hoster list - login failed, retry in 5 minutes"
                            )
                        )

                    self.periodical.set_interval(timedelta(minutes=5).total_seconds())

                else:
                    if reloading:
                        self.log_error(
                            self._(
                                "Could not reload hoster list - login failed, deactivating"
                            )
                        )

                    else:
                        self.log_error(
                            self._(
                                "Could not load hoster list - login failed, deactivating"
                            )
                        )

                    self.deactivate()

                return

        self.pyload.addon_manager.add_event("plugin_updated", self.plugins_updated)

        if refresh or not reloading:
            if not self.get_plugins(cached=False):
                self.fail_count += 1
                if self.fail_count < 3:
                    self.log_error(
                        self._(
                            "Failed to load hoster list for user `{}`, retry in 5 minutes"
                        ).format(self.user)
                    )
                    self.periodical.set_interval(timedelta(minutes=5).total_seconds())

                else:
                    self.log_error(
                        self._(
                            "Failed to load hoster list for user `{}`, deactivating"
                        ).format(self.user)
                    )
                    self.deactivate()

                return

        if self.fail_count:
            self.fail_count = 0

            interval = timedelta(hours=self.config.get("mh_interval", 12)).total_seconds()
            self.periodical.set_interval(interval)

        self._override()

    def deactivate(self):
        """
        Remove override for all plugins.
        """
        self.log_info(self._("Reverting back to default hosters"))

        self.pyload.addon_manager.remove_event(
            "plugin_updated", self.plugins_updated
        )

        self.periodical.stop()

        self.fail_count = 0

        if self.supported:
            self.log_debug(f"Unload: {', '.join(self.supported)}")
            for plugin in self.supported:
                self.unload_plugin(plugin)

        #: Reset pattern
        hdict = self.pyload.plugin_manager.plugins[self.plugintype][self.classname]

        hdict["pattern"] = getattr(self.pluginclass, "__pattern__", r"^unmatchable$")
        hdict["re"] = re.compile(hdict["pattern"])

    def update_accounts(self, user, password=None, options={}):
        super().update_accounts(user, password, options)
        if self.need_reactivate:
            interval = timedelta(hours=self.config.get("mh_interval", 12)).total_seconds()
            self.periodical.restart(interval, threaded=True, delay=2)

        self.need_reactivate = True

    def remove_account(self, user):
        self.deactivate()
        super().remove_account(user)
