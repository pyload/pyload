# -*- coding: utf-8 -*-

import operator
import os
import re
import sys
import time
from datetime import timedelta

from pyload import PKGDIR

from ..base.addon import BaseAddon, expose, threaded
from ..helpers import exists


class UpdateManager(BaseAddon):
    __name__ = "UpdateManager"
    __type__ = "addon"
    __version__ = "1.21"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("checkinterval", "int", "Check interval in hours", 6),
        ("autorestart", "bool", "Auto-restart pyLoad when required", True),
        ("checkonstart", "bool", "Check for updates on startup", True),
        ("checkperiod", "bool", "Check for updates periodically", True),
        ("reloadplugins", "bool", "Monitor plugin code changes in debug mode", True),
        ("nodebugupdate", "bool", "Don't update plugins in debug mode", False),
    ]

    __description__ = """Check for updates"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    _VERSION = re.compile(r'\s*__version__\s*=\s*("|\')([\d.]+)\1', re.M)

    # SERVER_URL     = "http://updatemanager.pyload.net"
    # SERVER_URL = "http://updatemanager-spyload.rhcloud.com"
    SERVER_URL = "https://raw.githubusercontent.com/pyload/updates/master/plugins.txt"
    MIN_CHECK_INTERVAL = timedelta(hours=3).total_seconds()  #: minimum is 3 hours

    def activate(self):
        if self.checkonstart:
            self.pyload.api.pause_server()
            self.update()

            if not self.do_restart:
                self.pyload.api.unpause_server()

        self.periodical.start(10)

    def init(self):
        self.info.update({"pyload": False, "plugins": False, "last_check": time.time()})
        self.mtimes = {}  #: Store modification time for each plugin
        self.event_map = {"all_downloads_processed": "all_downloads_processed"}

        if self.config.get("checkonstart"):
            self.pyload.api.pause_server()
            self.checkonstart = True
        else:
            self.checkonstart = False

        self.do_restart = False

    def all_downloads_processed(self):
        if self.do_restart:
            self.pyload.api.restart()

    def periodical_task(self):
        if self.pyload.debug:
            if self.config.get("reloadplugins"):
                self.autoreload_plugins()

            if self.config.get("nodebugupdate"):
                return

        if (
            self.config.get("checkperiod")
            and time.time()
            - max(
                self.MIN_CHECK_INTERVAL,
                timedelta(hours=self.config.get("checkinterval")).total_seconds(),
            )
            > self.info["last_check"]
        ):
            self.update()

        if self.do_restart:
            if (
                self.pyload.thread_manager.pause
                and not self.pyload.api.status_downloads()
            ):
                self.pyload.api.restart()

    @expose
    def autoreload_plugins(self):
        """
        Reload and reindex all modified plugins.
        """
        reloads = []
        modules = [
            m
            for m in sys.modules.values()
            if m
            and (
                m.__name__.startswith("pyload.plugins.")
                or m.__name__.startswith("userplugins.")
            )
            and m.__name__.count(".") >= 2
        ]
        for m in modules:
            root, plugin_type, plugin_name = m.__name__.rsplit(".", 2)
            plugin_id = (plugin_type, plugin_name)
            if plugin_type in self.pyload.plugin_manager.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not os.path.isfile(f):
                    continue

                mtime = os.path.getmtime(f)

                if plugin_id not in self.mtimes:
                    self.mtimes[plugin_id] = mtime

                elif self.mtimes[plugin_id] < mtime:
                    reloads.append(plugin_id)
                    self.mtimes[plugin_id] = mtime

        return True if self.pyload.plugin_manager.reload_plugins(reloads) else False

    def server_response(self, line=None):
        try:
            html = self.load(
                self.SERVER_URL, get={"v": self.pyload.api.get_server_version()}
            )

        except Exception:
            self.log_warning(
                self._("Unable to connect to the server to retrieve updates")
            )

        else:
            res = html.splitlines()

            if line is not None:
                try:
                    res = res[line]
                except IndexError:
                    res = None

            return res

    @expose
    @threaded
    def update(self):
        """
        Check for updates.
        """
        if self._update() != 2 or not self.config.get("autorestart"):
            return

        if not self.pyload.api.status_downloads():
            self.pyload.api.restart()
        else:
            self.log_warning(
                self._("pyLoad restart scheduled"),
                self._(
                    "Downloads are active, pyLoad restart postponed once the download is done"
                ),
            )
            self.pyload.api.pause_server()
            self.do_restart = True

    def _update(self):
        newversion = self.server_response(0)

        self.info["pyload"] = False
        self.info["last_check"] = time.time()

        if not newversion:
            exitcode = 0

        elif newversion == self.pyload.api.get_server_version():
            self.log_info(self._("pyLoad is up to date!"))
            exitcode = self.update_plugins()

        elif re.search(r"^\d+(?:\.\d+){0,3}[a-z]?$", newversion):
            self.log_info(
                self._("***  New pyLoad {} available  ***").format(newversion)
            )
            self.log_info(
                self._(
                    "***  Get it here: https://github.com/pyload/pyload/releases  ***"
                )
            )
            self.info["pyload"] = True
            exitcode = 3

        else:
            exitcode = 0

        #: Exit codes:
        #: -1 = No plugin updated, new pyLoad version available
        #:  0 = No plugin updated
        #:  1 = Plugins updated
        #:  2 = Plugins updated, but restart required
        return exitcode

    @expose
    def update_plugins(self):
        server_data = self.server_response()

        if not server_data or server_data[0] != self.pyload.api.get_server_version():
            return 0

        updated = self._update_plugins(server_data)

        if updated:
            self.log_info(self._("*** Plugins updated ***"))

            if self.pyload.plugin_manager.reload_plugins(updated):
                exitcode = 1
            else:
                self.log_warning(
                    self._("You have to restart pyLoad to use the updated plugins")
                )
                self.info["plugins"] = True
                exitcode = 2

            paused = self.pyload.thread_manager.pause
            self.pyload.api.pause_server()
            self.m.dispatch_event("plugin_updated", updated)
            if not paused:
                self.pyload.api.unpause_server()
        else:
            self.log_info(self._("All plugins are up to date!"))
            exitcode = 0

        #: Exit codes:
        #: 0 = No plugin updated
        #: 1 = Plugins updated
        #: 2 = Plugins updated, but restart required
        return exitcode

    def parse_updates(self, server_data):
        schema = server_data[2].split("|")

        if "BLACKLIST" in server_data:
            blacklist = server_data[server_data.index("BLACKLIST") + 1 :]
            updatelist = server_data[3 : server_data.index("BLACKLIST")]
        else:
            blacklist = []
            updatelist = server_data[3:]

        for l in updatelist, blacklist:
            nl = []
            for line in l:
                d = dict(zip(schema, line.split("|")))
                d["name"] = d["name"].rsplit(".py", 1)[0]
                nl.append(d)
            l[:] = nl

        updatelist = sorted(updatelist, key=operator.itemgetter("type", "name"))
        blacklist = sorted(blacklist, key=operator.itemgetter("type", "name"))

        return updatelist, blacklist

    def _update_plugins(self, server_data):
        """
        Check for plugin updates.
        """
        updated = []

        updatelist, blacklist = self.parse_updates(server_data)

        url = server_data[1]
        req = self.pyload.request_factory.get_request(self.classname)

        if blacklist:
            # NOTE: Protect UpdateManager from self-removing
            if os.name == "nt":
                # NOTE: Windows filesystem is case insensitive, make sure we do not
                # delete legitimate plugins
                whitelisted_plugins = [
                    (plugin["type"], plugin["name"].upper()) for plugin in updatelist
                ]
                blacklisted_plugins = [
                    (plugin["type"], plugin["name"])
                    for plugin in blacklist
                    if not (
                        plugin["name"] == self.classname
                        and plugin["type"] == self.__type__
                    )
                    and (plugin["type"], plugin["name"].upper())
                    not in whitelisted_plugins
                ]
            else:
                blacklisted_plugins = [
                    (plugin["type"], plugin["name"])
                    for plugin in blacklist
                    if not (
                        plugin["name"] == self.classname
                        and plugin["type"] == self.__type__
                    )
                ]

            c = 1
            l = len(blacklisted_plugins)
            for idx, plugin in enumerate(updatelist):
                if c > l:
                    break
                plugin_name = plugin["name"]
                plugin_type = plugin["type"]
                for t, n in blacklisted_plugins:
                    if n != plugin_name or t != plugin_type:
                        continue
                    updatelist.pop(idx)
                    c += 1
                    break

            for t, n in self.remove_plugins(blacklisted_plugins):
                self.log_info(
                    self._("Removed blacklisted plugin: {type} {name}").format(
                        type=t.upper(), name=n
                    )
                )

        userplugins = os.path.join(self.pyload.userdir, "userplugins")
        for plugin in updatelist:
            plugin_name = plugin["name"]
            plugin_type = plugin["type"]
            plugin_version = plugin["version"]

            plugins = getattr(
                self.pyload.plugin_manager, "{}Plugins".format(plugin_type.rstrip("s"))
            )  # TODO: Remove rstrip in 0.6.x)

            oldver = (
                float(plugins[plugin_name]["v"]) if plugin_name in plugins else None
            )
            try:
                newver = float(plugin_version)
            except ValueError:
                self.log_error(
                    self._("Error updating plugin: {} {}").format(
                        plugin_type.rstrip("s").upper(), plugin_name
                    ),
                    self._("Bad version number on the server"),
                )
                continue

            if not oldver:
                msg = "New plugin: {type} {name} (v{newver:.2f})"
            elif newver > oldver:
                msg = "New version of plugin: {type} {name} (v{oldver:.2f} -> v{newver:.2f})"
            else:
                continue

            self.log_info(
                msg.format(
                    type=plugin_type.rstrip(
                        "s"
                    ).upper(),  # TODO: Remove rstrip in 0.6.x
                    name=plugin_name,
                    oldver=oldver,
                    newver=newver,
                )
            )
            try:
                content = self.load(url.format(plugin + ".py"), decode=False, req=req)

                if req.code == 404:
                    raise Exception(self._("URL not found"))

                m = self._VERSION.search(content)
                if m is not None and m.group(2) == plugin_version:
                    with open(
                        os.path.join(userplugins, plugin_type, plugin_name + ".py"),
                        "wb",
                    ) as fp:
                        fp.write(content.encode())

                    updated.append((plugin_type, plugin_name))
                else:
                    raise Exception(self._("Version mismatch"))

            except Exception as exc:
                self.log_error(
                    self._("Error updating plugin: {} {}").format(
                        plugin_type.rstrip("s").upper(), plugin_name
                    ),
                    exc,
                )  # TODO: Remove rstrip in 0.6.x

        return updated

    @expose
    def remove_plugins(self, plugin_ids):
        """
        Delete plugins from disk.
        """
        if not plugin_ids:
            return

        removed = set()

        self.log_debug(f"Requested deletion of plugins: {plugin_ids}")

        for plugin_type, plugin_name in plugin_ids:
            userplugins = os.path.join(self.pyload.userdir, "plugins")
            rootplugins = os.path.join(PKGDIR, "plugins")

            for basedir in (userplugins, rootplugins):
                py_filename = os.path.join(basedir, plugin_type, plugin_name + ".py")
                pyc_filename = py_filename + "c"

                if plugin_type == "addon":
                    try:
                        self.m.deactivate_addon(plugin_name)

                    except Exception as exc:
                        self.log_debug(
                            exc,
                            exc_info=self.pyload.debug > 1,
                            stack_info=self.pyload.debug > 2,
                        )

                for filename in (py_filename, pyc_filename):
                    if not exists(filename):
                        continue

                    try:
                        os.remove(filename)

                    except OSError as exc:
                        self.log_warning(
                            self._("Error removing `{}`").format(filename), exc
                        )

                    else:
                        plugin_id = (plugin_type, plugin_name)
                        removed.add(plugin_id)

        #: Return a list of the plugins successfully removed
        return list(removed)
