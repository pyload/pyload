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

    @author: mkaay
    @interface-version: 0.1
"""

from module.network.Request import getURL
from module.plugins.Hook import Hook

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

    def coreReady(self):
    #@TODO check plugins, restart, and other stuff
        pass

    def periodical(self):
        update = self.checkForUpdate()
        if self.updated:
            self.log.info(_("*** Plugins were updated, please restart pyLoad ***"))
        if not update:
            self.checkPlugins()


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
            self.log.error(_("Not able to connect server"))
            return False


    def checkPlugins(self):
        """ checks for plugins updates"""

        string = ""
        
        string += self.createUpdateList(self.core.pluginManager.crypterPlugins, "crypter")
        string += self.createUpdateList(self.core.pluginManager.hosterPlugins, "hoster")
        string += self.createUpdateList(self.core.pluginManager.containerPlugins, "container")
        string += self.createUpdateList(self.core.pluginManager.accountPlugins, "account")
        string += self.createUpdateList(self.core.pluginManager.hookPlugins, "hook")
        string += self.createUpdateList(self.core.pluginManager.captchaPlugins, "captcha")

        try:
            updates = getURL("updateurl", post={"plugins": string})
        except:
            self.log.warning(_("Plugins could not be updated"))
            updates = ""

        updates = updates.splitlines()

        for plugin in updates:
            type, name, url = plugin.split("|")
            print type, name, url
            #@TODO save url content to disk

    def createUpdateList(self, plugins, type):
        """ create string list for update check """
        string = ""
        for name,plugin in plugins.iteritems():
            string += "%s|%s|%s\n" % (type, name, plugin["v"])

        return string