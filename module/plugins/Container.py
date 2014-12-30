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

from module.plugins.Crypter import Crypter

from os.path import join, exists, basename
from os import remove
import re

class Container(Crypter):
    __name__ = "Container"
    __version__ = "0.1"
    __pattern__ = None
    __type__ = "container"
    __description__ = """Base container plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")


    def preprocessing(self, thread):
        """prepare"""

        self.setup()
        self.thread = thread
        
        self.loadToDisk()

        self.decrypt(self.pyfile)
        self.deleteTmp()
        
        self.createPackages()
    

    def loadToDisk(self):
        """loads container to disk if its stored remotely and overwrite url, 
        or check existent on several places at disk"""
        
        if self.pyfile.url.startswith("http"):
            self.pyfile.name = re.findall("([^\/=]+)", self.pyfile.url)[-1]
            content = self.load(self.pyfile.url)
            self.pyfile.url = join(self.config["general"]["download_folder"], self.pyfile.name)
            f = open(self.pyfile.url, "wb" )
            f.write(content)
            f.close()
            
        else:
            self.pyfile.name = basename(self.pyfile.url)
            if not exists(self.pyfile.url):
                if exists(join(pypath, self.pyfile.url)):
                    self.pyfile.url = join(pypath, self.pyfile.url)
                else:
                    self.fail(_("File not exists."))
      

    def deleteTmp(self):
        if self.pyfile.name.startswith("tmp_"):
            remove(self.pyfile.url)

        
