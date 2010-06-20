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

from module.plugins.Plugin import Plugin

class Hoster(Plugin):
    __name__ = "Hoster"
    __version__ = "0.1"
    __pattern__ = None
    __type__ = "hoster"
    __description__ = """Base hoster plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def preparePlugin(self, thread):
        self.thread = thread
        self.usePremium = False
    
    def getFileName(self):
        try:
            return re.findall("([^\/=]+)", self.pyfile.url)[-1]
        except:
            return self.pyfile.url[:20]
    
    def isOnline(self):
        return True
    
    def multiDownload(self):
        return True
    
    def prepareDownload(self):
        pass
    
    def startDownload(self):
        self.req.download(self.pyfile.url, self.pyfile.folder)
    
    def verifyDownload(self):
        return True
    
    def wait(self, until=None, reconnect=False):
        self.pyfile.status.want_reconnect = reconnect
        self.pyfile.status.waituntil = until
        if not until:
            self.pyfile.status.waituntil = 0
        
