# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""

import sys
import re
from os import stat
from os.path import join, exists
from time import time

from module.plugins.PluginManager import IGNORE
from module.network.RequestFactory import getURL
from module.plugins.Addon import threaded, Expose, Addon

class UpdateManager(Addon):
    __name__ = "UpdateManager"
    __version__ = "0.12"
    __description__ = """checks for updates"""
    __config__ = [("activated", "bool", "Activated", "True"),
        ("interval", "int", "Check interval in minutes", "360"),
        ("debug", "bool", "Check for plugin changes when in debug mode", False)]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("ranan@pyload.org")

    @property
    def debug(self):
        return self.core.debug and self.getConfig("debug")


    def setup(self):
        if self.debug:
            self.logDebug("Monitoring file changes")
            self.interval = 4
            self.last_check = 0 #timestamp of updatecheck
            self.old_periodical = self.periodical
            self.periodical = self.checkChanges
            self.mtimes = {}  #recordes times
        else:
            self.interval = self.getConfig("interval") * 60

        self.updated = False
        self.reloaded = True

        self.info = {"pyload": False, "plugins": False}

    @threaded
    def periodical(self):

        if self.core.version.endswith("-dev"):
            self.logDebug("No update check performed on dev version.")
            return

        update = self.checkForUpdate()
        if update:
            self.info["pyload"] = True
        else:
            self.log.info(_("No Updates for pyLoad"))
            self.checkPlugins()

        if self.updated and not self.reloaded:
            self.info["plugins"] = True
            self.log.info(_("*** Plugins have been updated, please restart pyLoad ***"))
        elif self.updated and self.reloaded:
            self.log.info(_("Plugins updated and reloaded"))
            self.updated = False
        else:
            self.log.info(_("No plugin updates available"))

    @Expose
    def recheckForUpdates(self):
        """recheck if updates are available"""
        self.periodical()

    def checkForUpdate(self):
        """checks if an update is available"""

        try:
            version_check = getURL("http://get.pyload.org/check/%s/" % self.core.api.getServerVersion())
            if version_check == "":
                return False
            else:
                self.log.info(_("***  New pyLoad Version %s available  ***") % version_check)
                self.log.info(_("***  Get it here: http://pyload.org/download  ***"))
                return True
        except:
            self.log.warning(_("Not able to connect server for updates"))
            return False


    def checkPlugins(self):
        """ checks for plugins updates"""

        # plugins were already updated
        if self.info["plugins"]: return

        try:
            updates = getURL("http://get.pyload.org/plugins/check/")
        except:
            self.log.warning(_("Not able to connect server for updates"))
            return False

        updates = updates.splitlines()
        reloads = []

        vre = re.compile(r'__version__.*=.*("|\')([0-9.]+)')

        for plugin in updates:
            path, version = plugin.split(":")
            prefix, filename = path.split("/")

            if filename.endswith(".pyc"):
                name = filename[:filename.find("_")]
            else:
                name = filename.replace(".py", "")

	    #TODO: obsolete
            if prefix.endswith("s"):
                type = prefix[:-1]
            else:
                type = prefix

            plugins = self.core.pluginManager.getPlugins(type)

            if name in plugins:
                if float(plugins[name].version) >= float(version):
                    continue

            if name in IGNORE or (type, name) in IGNORE:
                continue

            self.log.info(_("New version of %(type)s|%(name)s : %(version).2f") % {
                "type": type,
                "name": name,
                "version": float(version)
            })

            try:
                content = getURL("http://get.pyload.org/plugins/get/" + path)
            except Exception, e:
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

        self.reloaded = self.core.pluginManager.reloadPlugins(reloads)

    def checkChanges(self):

        if self.last_check + self.getConfig("interval") * 60 < time():
            self.old_periodical()
            self.last_check = time()

        modules = filter(
            lambda m: m and (m.__name__.startswith("module.plugins.") or m.__name__.startswith("userplugins.")) and m.__name__.count(".") >= 2,
            sys.modules.itervalues())

        reloads = []

        for m in modules:
            root, type, name = m.__name__.rsplit(".", 2)
            id = (type, name)
            if type in self.core.pluginManager.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not exists(f): continue

                mtime = stat(f).st_mtime

                if id not in self.mtimes:
                    self.mtimes[id] = mtime
                elif self.mtimes[id] < mtime:
                    reloads.append(id)
                    self.mtimes[id] = mtime

        self.core.pluginManager.reloadPlugins(reloads)
