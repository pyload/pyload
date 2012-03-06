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
    @interface-version: 0.2
"""

from os import makedirs
from os import listdir
from os.path import exists
from os.path import join
from os.path import isfile
from shutil import move
import time

from module.plugins.Addon import Addon

class HotFolder(Addon):
    __name__ = "HotFolder"
    __version__ = "0.1"
    __description__ = """observe folder and file for changes and add container and links"""
    __config__ = [ ("activated", "bool", "Activated" , "False"),
                   ("folder", "str", "Folder to observe", "container"),
                   ("watch_file", "bool", "Observe link file", "False"),
                   ("keep", "bool", "Keep added containers", "True"),
                   ("file", "str", "Link file", "links.txt")]
    __threaded__ = []
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.de")
    
    def setup(self):
        self.interval = 10
        
    def periodical(self):
        
        if not exists(join(self.getConfig("folder"), "finished")):
            makedirs(join(self.getConfig("folder"), "finished"))
          
        if self.getConfig("watch_file"):

            if not exists(self.getConfig("file")):
                f = open(self.getConfig("file"), "wb")
                f.close()
            
            
            f = open(self.getConfig("file"), "rb")
            content = f.read().strip()
            f.close()
            f = open(self.getConfig("file"), "wb")
            f.close()
            if content:
                name = "%s_%s.txt" % (self.getConfig("file"), time.strftime("%H-%M-%S_%d%b%Y") )

                f = open(join(self.getConfig("folder"), "finished", name), "wb")
                f.write(content)
                f.close()

                self.core.api.addPackage(f.name, [f.name], 1)
              
        for f in listdir(self.getConfig("folder")):
            path = join(self.getConfig("folder"), f)
            
            if not isfile(path) or f.endswith("~") or f.startswith("#") or f.startswith("."):
                continue
            
            newpath = join(self.getConfig("folder"), "finished", f if self.getConfig("keep") else "tmp_"+f)
            move(path, newpath)
            
            self.log.info(_("Added %s from HotFolder") % f)
            self.core.api.addPackage(f, [newpath], 1)
            
        