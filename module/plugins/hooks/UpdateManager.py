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
    @interface-version: 0.1
"""
import re
from os.path import join

from module.network.RequestFactory import getURL
from module.plugins.Hook import threaded, Expose, Hook

class UpdateManager(Hook):
    __name__ = "UpdateManager"
    __version__ = "0.1"
    __description__ = """checks for updates"""
    __config__ = [("activated", "bool", "Activated", "True"),
                  ("interval", "int", "Check interval in minutes", "360")]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("ranan@pyload.org")

    def setup(self):
        self.interval = self.getConfig("interval") * 60
        self.updated = False
        self.reloaded = True

        self.info = {"pyload": False, "plugins": False}

    @threaded
    def periodical(self):
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
        else:
            self.log.info(_("No plugin updates available"))

    @Expose
    def recheckForUpdates(self):
        """recheck if updates are available"""
        self.periodical()

    def checkForUpdate(self):
        """checks if an update is available"""

        try:
            version_check = getURL("http://get.pyload.org/check/%s/" % self.core.server_methods.get_server_version())
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

        try:
            updates = getURL("http://get.pyload.org/plugins/check/")
        except:
            self.log.warning(_("Not able to connect server for updates"))
            return False

        updates = updates.splitlines()

        vre = re.compile(r'__version__.*=.*("|\')([0-9.]+)')

        for plugin in updates:
            path, version = plugin.split(":")
            prefix, name = path.split("/")

            if name.endswith(".pyc"):
                tmp_name = name[:name.find("_")]
            else:
                tmp_name = name.replace(".py", "")

            if prefix.endswith("s"):
                type = prefix[:-1]
            else:
                type = prefix

            plugins = getattr(self.core.pluginManager, "%sPlugins" % type)

            if plugins.has_key(tmp_name):
                if float(plugins[tmp_name]["v"]) >= float(version):
                    continue

            self.log.info(_("New version of %(type)s|%(name)s : %(version).2f") % {
                "type": type,
                "name": name,
                "version": float(version)
            })

            try:
                content = getURL("http://get.pyload.org/plugins/get/" + path)
            except:
                self.logWarning(_("Error when updating %s") % name)
                continue

            m = vre.search(content)
            if not m or m.group(2) != version:
                self.logWarning(_("Error when updating %s") % name)
                continue

            f = open(join("userplugins", prefix, name), "wb")
            f.write(content)
            f.close()
            self.updated = True

        self.reloaded = False
        self.core.pluginManager.reloadPlugins()
