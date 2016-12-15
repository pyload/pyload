# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals

from builtins import str
from builtins import zip
import sys
import re
from os import stat
from os.path import join, exists
from time import time

from pyload.configparser import IGNORE
from pyload.network.requestfactory import getURL
from pyload.plugins.hook import threaded, Expose, Hook


class UpdateManager(Hook):
    __name__ = "UpdateManager"
    __version__ = "0.15"
    __description__ = """Checks for updates"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("interval", "int", "Check interval in minutes", 480),
                  ("debug", "bool", "Check for plugin changes when in debug mode", False)]
    __author_name__ = "RaNaN"
    __author_mail__ = "ranan@pyload.net"

    URL = "http://get.pyload.net/check2/%s/"
    MIN_TIME = 3 * 60 * 60  # 3h minimum check interval

    @property
    def debug(self):
        return self.pyload.debug and self.getConfig("debug")

    def setup(self):
        if self.debug:
            self.logDebug("Monitoring file changes")
            self.interval = 4
            self.last_check = 0  # timestamp of updatecheck
            self.old_periodical = self.periodical
            self.periodical = self.checkChanges
            self.mtimes = {}  # recordes times
        else:
            self.interval = max(self.getConfig("interval") * 60, self.MIN_TIME)

        self.updated = False
        self.reloaded = True
        self.version = "None"

        self.info = {"pyload": False, "plugins": False}

    @threaded
    def periodical(self):

        updates = self.checkForUpdate()
        if updates:
            self.checkPlugins(updates)

        if self.updated and not self.reloaded:
            self.info["plugins"] = True
            self.logInfo(_("*** Plugins have been updated, please restart pyLoad ***"))
        elif self.updated and self.reloaded:
            self.logInfo(_("Plugins updated and reloaded"))
            self.updated = False
        elif self.version == "None":
            self.logInfo(_("No plugin updates available"))

    @Expose
    def recheckForUpdates(self):
        """recheck if updates are available"""
        self.periodical()

    def checkForUpdate(self):
        """checks if an update is available, return result"""

        try:
            if self.version == "None":  # No updated known
                version_check = getURL(self.URL % self.pyload.api.getServerVersion()).splitlines()
                self.version = version_check[0]

                # Still no updates, plugins will be checked
                if self.version == "None":
                    self.logInfo(_("No Updates for pyLoad"))
                    return version_check[1:]

            self.info["pyload"] = True
            self.logInfo(_("***  New pyLoad Version %s available  ***") % self.version)
            self.logInfo(_("***  Get it here: https://github.com/pyload/pyload/releases  ***"))

        except Exception:
            self.logWarning(_("Not able to connect server for updates"))

        return None  # Nothing will be done

    def checkPlugins(self, updates):
        """ checks for plugins updates"""

        # plugins were already updated
        if self.info["plugins"]:
            return

        reloads = []

        vre = re.compile(r'__version__.*=.*("|\')([0-9.]+)')
        url = updates[0]
        schema = updates[1].split("|")
        updates = updates[2:]

        for plugin in updates:
            info = dict(list(zip(schema, plugin.split("|"))))
            filename = info["name"]
            prefix = info["type"]
            version = info["version"]

            if filename.endswith(".pyc"):
                name = filename[:filename.find("_")]
            else:
                name = filename.replace(".py", "")

            #TODO: obsolete in 0.5.0
            if prefix.endswith("s"):
                type = prefix[:-1]
            else:
                type = prefix

            plugins = getattr(self.pyload.pluginManager, "%sPlugins" % type)

            if name in plugins:
                if float(plugins[name]["v"]) >= float(version):
                    continue

            if name in IGNORE or (type, name) in IGNORE:
                continue

            self.logInfo(_("New version of %(type)s|%(name)s : %(version).2f") % {
                "type": type,
                "name": name,
                "version": float(version)
            })

            try:
                content = getURL(url % info)
            except Exception as e:
                self.logWarning(_("Error when updating %s") % filename, str(e))
                continue

            m = vre.search(content)
            if not m or m.group(2) != version:
                self.logWarning(_("Error when updating %s") % name, _("Version mismatch"))
                continue

            f = open(join("userplugins", prefix, filename), "wb")
            f.write(content)
            f.close()
            self.updated = True

            reloads.append((prefix, name))

        self.reloaded = self.pyload.pluginManager.reloadPlugins(reloads)

    def checkChanges(self):

        if self.last_check + max(self.getConfig("interval") * 60, self.MIN_TIME) < time():
            self.old_periodical()
            self.last_check = time()

        modules = [m for m in sys.modules.values() if m and (m.__name__.startswith("module.plugins.") or m.__name__.startswith(
                "userplugins.")) and m.__name__.count(".") >= 2]

        reloads = []

        for m in modules:
            root, type, name = m.__name__.rsplit(".", 2)
            id = (type, name)
            if type in self.pyload.pluginManager.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not exists(f):
                    continue

                mtime = stat(f).st_mtime

                if id not in self.mtimes:
                    self.mtimes[id] = mtime
                elif self.mtimes[id] < mtime:
                    reloads.append(id)
                    self.mtimes[id] = mtime

        self.pyload.pluginManager.reloadPlugins(reloads)
