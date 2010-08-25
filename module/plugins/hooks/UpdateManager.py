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
    __config__ = [ ("activated", "bool", "Activated" , "True"),
                   ("interval", "int", "Check interval in minutes" , "180")]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("ranan@pyload.org")

    def setup(self):
        self.interval = self.getConfig("interval") * 60
        
    def coreReady(self):
        #@TODO check plugins, restart, and other stuff
        pass
    
    def periodical(self):
        self.checkForUpdate()
        
        
    def checkForUpdate(self):
        """ checks if an update is available"""
        
        try:
            version_check = getURL("http://get.pyload.org/check/%s/" % self.core.server_methods.get_server_version() )
            if version_check == "":
                self.log.info(_("No Updates for pyLoad"))
                return False
            else:
                self.log.info(_("***  New pyLoad Version %s available  ***") % version_check)
                self.log.info(_("***  Get it here: http://get.pyload.org/get/  ***"))
                return True
        except:
            self.log.error(_("Not able to connect server"))

        