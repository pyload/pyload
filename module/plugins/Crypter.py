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

from os.path import join, exists, basename

class Crypter(Plugin):
    __name__ = "Crypter"
    __version__ = "0.1"
    __pattern__ = None
    __type__ = "container"
    __description__ = """Base crypter plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def __init__(self, pyfile):
        Plugin.__init__(self, pyfile)
        
        self.packages = [] #put all packages here [ .. (name, folder, [urls]) ..]
    
    #----------------------------------------------------------------------
    def preprocessing(self, thread):
        """prepare"""
        self.thread = thread

        self.decrypt(self.pyfile)
        
        self.createPackages()
        
    
    #----------------------------------------------------------------------
    def loadToDisk(self):
        """loads container to disk if its stored remotely and overwrite url, 
        or check existent on several places at disk"""
        
        if self.pyfile.url.startswith("http://"):
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
        

    #----------------------------------------------------------------------
    def createPackages(self):
        """ create new packages from self.packages """
        i = 0
        for pack in self.packages:

            self.log.info(_("Parsed package %s with %s links") % (pack[0], len(pack[1]) ) )
            
            if i == 0:
                # replace current package with new one
                self.pyfile.package().name = pack[0]
                self.pyfile.package().folder = pack[2]
                
                self.core.files.addLinks(pack[1], self.pyfile.package().id)
                
                self.pyfile.package().sync()
            else:
                self.core.server_methods.add_package(pack[0], pack[1])
            
            i += 1
            