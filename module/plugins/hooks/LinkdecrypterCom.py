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

    @author: zoidberg
"""

import re

from module.plugins.Hook import Hook
from module.network.RequestFactory import getURL
from module.utils import remove_chars

class LinkdecrypterCom(Hook):
    __name__ = "LinkdecrypterCom"
    __version__ = "0.14"
    __description__ = """linkdecrypter.com - regexp loader"""
    __config__ = [ ("activated", "bool", "Activated" , "True") ]
    __author_name__ = ("zoidberg")
    
    def coreReady(self):
        page = getURL("http://linkdecrypter.com/")
        m = re.search(r'<b>Supported</b>: <i>([^+<]*)', page)
        if not m:
            self.logError(_("Crypter list not found"))
            return
            
        online = m.group(1).split(', ')            
        builtin = [ name.lower() for name in self.core.pluginManager.crypterPlugins.keys() ]
        builtin.extend([ "downloadserienjunkiesorg" ])
               
        online = [ crypter.replace(".", "\\.") for crypter in online if remove_chars(crypter, "-.") not in builtin ]
        if not online:
            self.logError(_("Crypter list is empty"))
            return
             
        regexp = r"https?://([^.]+\.)*?(%s)/.*" % "|".join(online)

        dict = self.core.pluginManager.crypterPlugins[self.__name__]
        dict["pattern"] = regexp
        dict["re"] = re.compile(regexp)
        
        self.logDebug("REGEXP: " + regexp)