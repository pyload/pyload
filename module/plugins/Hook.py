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
    @interface-version: 0.2
"""



class Hook():
    __name__ = "Hook"
    __version__ = "0.2"
    __type__ = "hook"
    __description__ = """interface for hook"""
    __author_name__ = ("mkaay", "RaNaN")
    __author_mail__ = ("mkaay@mkaay.de", "RaNaN@pyload.org")
    
    def __init__(self, core):
        self.core = core 
        self.log = core.log
        
        self.setup()
               
    def setup(self):
        pass
    
    def isActivated(self):
        return self.config["activated"]
    
    def coreReady(self):
        pass
    
    def downloadStarts(self, pyfile):
        pass
    
    def downloadFinished(self, pyfile):
        pass
    
    def packageFinished(self, pypack):
        pass
    
    def beforeReconnecting(self, ip):
        pass
    
    def afterReconnecting(self, ip):
        pass
