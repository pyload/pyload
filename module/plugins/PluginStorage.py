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
"""

class PluginStorage():
    def getStorage(self, key=None, default=None):
        if key is not None:
            return self.core.db.getStorage(self.__name__, key) or default
        return self.core.db.getStorage(self.__name__, key)
    
    def setStorage(self, key, value):
        self.core.db.setStorage(self.__name__, key, value)
        
    def delStorage(self, key):
        self.core.db.delStorage(self.__name__, key)
