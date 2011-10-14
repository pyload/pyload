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
"""

import os
from os.path import join

from subprocess import Popen, PIPE

from module.plugins.hooks.ExtractArchive import AbtractExtractor
from module.utils import save_join

try:
    import pexpect #used for progress
    PEXPECT = True
except ImportError:
    PEXPECT = False

import re

class UnRar(AbtractExtractor):
    __name__ = "UnRar"
    __version__ = "0.1"

    re_splitfile = re.compile("(.*)\.part(\d+)\.rar$")

    @staticmethod
    def checkDeps():
        return True #TODO

    @staticmethod
    def getTargets(files_ids):
        result = []

        for file, id in files_ids:
            if not file.endswith(".rar"): continue

            match = UnRar.re_splitfile.findall(file)
            if match:
                #only add first parts
                if int(match[0][1]) == 1:
                    result.append((file, id))
            else:
                result.append((file, id))

        return result


    def init(self):
        self.passwordProtected = False
        self.headerProtected = False  #list files will not work without password
        self.smallestFile = None  #small file to test passwords
        self.password = ""  #save the correct password

    def checkArchive(self):
        p = self.call_unrar("l", "-v", self.file)
        out, err = p.communicate()
        if "Corrupt file or wrong password." in err:
            self.passwordProtected = True
            self.headerProtected = True
            return True

        self.listContent()
        if not self.files:
            self.m.archiveError("Empty Archive")

        return False

    def checkPassword(self, password):
        if not self.passwordProtected: return True

        if self.headerProtected:
            p = self.call_unrar("l", "-v", self.file, password=password)
            out, err = p.communicate()
            if "Corrupt file or wrong password." in err:
                return False

        return True


    def extract(self, progress, password=None):
        command = "x" if self.fullpath else "e"

        if PEXPECT:
            p = self.call_unrar(command, self.file, self.out, password=password, pexpect=True)
            #renice(p.pid, self.renice)

            cpl = p.compile_pattern_list([pexpect.EOF, "(\d+)\s?%"])
            while True:
                i = p.expect_list(cpl, timeout=None)
                if i == 0: # EOF
                    break #exited
                elif i == 1:
                    perc =  p.match.group(1)
                    progress(int(perc))
            # pexpect thinks process is still alive (just like popen) - very strange behavior
            p.terminated = True

        else:
            #subprocess - no progress
            p = self.call_unrar(command, self.file, self.out, password=password)
            renice(p.pid, self.renice)

            progress(0)
            out, err = p.communicate() #wait for process
            progress(100)

        #TODO, check for errors


    def getDeleteFiles(self):
        #TODO
        return []

    def listContent(self):
        command = "vb" if self.fullpath else "lb"
        p = self.call_unrar(command, "-v", self.file, password=self.password)
        out, err = p.communicate()

        result = set()

        for f in out.splitlines():
            f = f.strip()
            result.add(save_join(self.out, f))

        self.files = result


    def call_unrar(self, command, *xargs, **kwargs):
        if os.name == "nt":
            cmd = join(pypath, "UnRAR.exe")
        else:
            cmd = "unrar"

        args = []

        #overwrite flag
        args.append("-o+") if self.overwrite else args.append("-o-")

        # assume yes on all queries
        args.append("-y")

        #set a password
        if "password" in kwargs and kwargs["password"]:
            args.append("-p%s" % kwargs["password"])
        else:
            args.append("-p-")


        #NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [cmd, command] + args + list(xargs)
        self.m.logDebug(" ".join(call))

        if PEXPECT and "pexpect" in kwargs:
            #use pexpect if available
            p = pexpect.spawn(" ".join(call))
        else:
            p = Popen(call, stdout=PIPE, stderr=PIPE)

        return p


def renice(pid, value):
    if os.name != "nt" and value:
        try:
            Popen(["renice", str(value), str(pid)], stdout=PIPE, stderr=PIPE, bufsize=-1)
        except:
            print "Renice failed"