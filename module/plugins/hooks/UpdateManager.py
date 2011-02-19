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
from os.path import join

from module.network.RequestFactory import getURL
from module.plugins.Hook import threaded, Hook

class UpdateManager(Hook):
    __name__ = "UpdateManager"
    __version__ = "0.1"
    __description__ = """checks for updates"""
    __config__ = [("activated", "bool", "Activated", "True"),
                  ("interval", "int", "Check interval in minutes", "180")]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("ranan@pyload.org")

    def setup(self):
        self.interval = self.getConfig("interval") * 60
        self.updated = False

    @threaded
    def periodical(self):
        update = self.checkForUpdate()
        if not update:
            self.checkPlugins()
        if self.updated:
            self.log.info(_("*** Plugins have been updated, please restart pyLoad ***"))
        else:
            self.log.info(_("No plugin updates available"))

    def checkForUpdate(self):
        """ checks if an update is available"""

        try:
            version_check = getURL("http://get.pyload.org/check/%s/" % self.core.server_methods.get_server_version())
            if version_check == "":
                self.log.info(_("No Updates for pyLoad"))
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

            content = getURL("http://get.pyload.org/plugins/get/" + path)
            f = open(join("userplugins", prefix, name), "wb")
            f.write(content)
            f.close()
            self.updated = True