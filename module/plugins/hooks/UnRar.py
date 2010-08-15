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

from __future__ import with_statement

from module.plugins.Hook import Hook
from module.pyunrar import Unrar, WrongPasswordError, CommandError, UnknownError

from os.path import exists, join
from os import remove
import re

class UnRar(Hook):
    __name__ = "UnRar"
    __version__ = "0.1"
    __description__ = """unrar"""
    __config__ = [ ("activated", "bool", "Activated", False),
                   ("fullpath", "bool", "extract full path", True),
                   ("overwrite", "bool", "overwrite files", True),
                   ("passwordfile", "str", "unrar passoword file", "unrar_passwords.txt"),
                   ("deletearchive", "bool", "delete archives when done", False) ]
    __threaded__ = ["packageFinished"]
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def setup(self):
        self.comments = ["# one password each line"]
        self.passwords = []
        if exists(self.getConfig("passwordfile")):
            with open(self.getConfig("passwordfile"), "r") as f:
                for l in f.readlines():
                    l = l.strip("\n\r")
                    if l and not l.startswith("#"):
                        self.passwords.append(l)
        else:
            with open(self.getConfig("passwordfile"), "w") as f:
                f.writelines(self.comments)
        self.re_splitfile = re.compile("(.*)\.part(\d+)\.rar$")
    
    def addPassword(self, pw):
        if not pw in self.passwords:
            self.passwords.insert(0, pw)
            with open(self.getConfig("passwordfile"), "w") as f:
                f.writelines(self.comments)
                f.writelines(self.passwords)
        
    def removeFiles(self, pack, fname):
        if not self.getConfig("deletearchive"):
            return
        m = self.re_splitfile.search(fname)
                
        download_folder = self.core.config['general']['download_folder']
        if self.core.config['general']['folder_per_package']:
            folder = join(download_folder, pack.folder.decode(sys.getfilesystemencoding()))
        else:
            folder = download_folder
        if m:
            nre = re.compile("%s\.part\d+\.rar" % m.group(1))
            for fid, data in pack.getChildren().iteritems():
                if nre.match(data["name"]):
                    remove(join(folder, data["name"]))
        elif not m and fname.endswith(".rar"):
            nre = re.compile("^%s\.r..$" % fname.replace(".rar",""))
            for fid, data in pack.getChildren().iteritems():
                if nre.match(data["name"]):
                    remove(join(folder, data["name"]))
    
    def packageFinished(self, pack):
        if pack.password:
            self.addPassword(pack.password)
        files = []
        for fid, data in pack.getChildren().iteritems():
            m = self.re_splitfile.search(data["name"])
            if m and int(m.group(2)) == 1:
                files.append((fid,m.group(0)))
            elif not m and data["name"].endswith(".rar"):
                files.append((fid,data["name"]))
        
        for fid, fname in files:
            pyfile = self.core.files.getFile(fid)
            pyfile.setStatus("custom")
            def s(p):
                pyfile.alternativePercent = p
                
            download_folder = self.core.config['general']['download_folder']
            if self.core.config['general']['folder_per_package']:
                folder = join(download_folder, pack.folder.decode(sys.getfilesystemencoding()))
            else:
                folder = download_folder
            
            u = Unrar(join(folder, fname))
            try:
                success = u.crackPassword(passwords=self.passwords, statusFunction=s, overwrite=True, destination=folder, fullPath=self.getConfig("fullpath"))
            except WrongPasswordError:
                continue
            except CommandError, e:
                if re.search("Cannot find volume", e.stderr):
                    continue
                try:
                    if e.getExitCode() == 1 and len(u.listContent(u.getPassword())) == 1:
                        self.removeFiles(pack, fname)
                except:
                    continue
            except UnknownError:
                continue
            else:
                if success:
                    self.removeFiles(pack, fname)
            finally:
                pyfile.alternativePercent = None
                pyfile.setStatus("finished")

