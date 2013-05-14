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
    
    @author: mmichaa (Michael Nowak)
"""

import os
import re
from glob import glob
from subprocess import Popen, PIPE
from string import digits

from module.utils import save_join, decode, fs_encode
from module.plugins.internal.AbstractExtractor import AbtractExtractor, WrongPassword, ArchiveError, CRCError

class AbstractSevenZip(AbtractExtractor):
    # name of the binary
    cmd = "7z"

    # should be set in sub-classes
    re_singlefile = None
    re_splitfile = None
    re_partfile = None

    # presets
    re_filelist = re.compile(r"([\d\:]+)\s+([\d\:]+)\s+([\w\.]+)\s+(\d+)\s+(\d+)\s+(.+)")
    re_wrongpwd = re.compile("(Can not open encrypted archive|Wrong password)", re.I)
    re_encrypted = re.compile(r"Encrypted\s+\=\s+\+", re.I)

    @classmethod
    def checkDeps(cls):
        if os.name == "nt": # who cares nt-os :P
            cls.cmd = save_join(pypath, "7z.exe")
            p = Popen([cls.cmd], stdout=PIPE, stderr=PIPE)
            p.communicate()
        else:
            p = Popen([cls.cmd], stdout=PIPE, stderr=PIPE)
            p.communicate()

        return True

    @classmethod
    def getTargets(cls, files_ids):
        result = []
        basenames = []

        for file, id in files_ids:
            match = None
            match = match or cls.re_splitfile.match(file)
            match = match or cls.re_partfile.match(file)
            match = match or cls.re_singlefile.match(file)
            if match:
                basename = os.path.basename(match.group(1))
                #import pdb; pdb.set_trace()
                if basename not in basenames:
                    basenames.append(basename)
                    result.append((file, id))

        return result


    def init(self):
        self.passwordProtected = False
        self.headerProtected = False  # list files will not work without password
        self.smallestFile = None  # small file to test passwords
        self.password = ""  # save the correct password

    def checkArchive(self):
        p = self.call_7z("l", "-slt", fs_encode(self.file))
        out, err = p.communicate()
        code = p.returncode

        # check if output or error macthes the 'wrong password'-Regexp
        if self.re_wrongpwd.search(out):
            self.passwordProtected = True
            self.headerProtected = True
            return True

        # check if output matches 'Encrypted = +'
        if self.re_encrypted.search(out):
            self.passwordProtected = True
            return True

        # check if archive is empty
        self.listContent()
        if not self.files:
            raise ArchiveError("Empty Archive")

        return False

    def checkPassword(self, password):
        # at this point we can only verify header protected files
        if self.headerProtected:
            p = self.call_7z("l", fs_encode(self.file), password=password)
            out, err = p.communicate()
            code = p.returncode
            if code != 0:
                return False

        return True


    def extract(self, progress, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_7z(command, '-o' + self.out, fs_encode(self.file), password=password)
        renice(p.pid, self.renice)

        progress(0)

        out, err = p.communicate()
        code = p.returncode

        progress(100)

        if "CRC failed" in out:
            raise CRCError
        elif p.returncode != 0:
            raise ArchiveError("Process terminated unsuccessful")

        if not self.files:
            self.password = password
            self.listContent()


    def listContent(self):
        command = "l" if self.fullpath else "l"
        p = self.call_7z(command, fs_encode(self.file), password=self.password)
        out, err = p.communicate()
        code = p.returncode

        if "Can not open" in err:
            raise ArchiveError("Cannot open file")

        if code != 0:
            raise ArchiveError("Process terminated unsuccessful")

        result = set()

        for groups in self.re_filelist.findall(out):
            f = groups[-1].strip()
            result.add(save_join(self.out, f))

        self.files = result


    def call_7z(self, command, *xargs, **kwargs):
        args = []

        #overwrite flag
        if self.overwrite:
            args.append("-y")

        #set a password
        if "password" in kwargs and kwargs["password"]:
            args.append("-p%s" % kwargs["password"])
        else:
            args.append("-p-")

        #NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [self.cmd, command] + args + list(xargs)
        self.m.logDebug(" ".join([decode(arg) for arg in call]))

        p = Popen(call, stdout=PIPE, stderr=PIPE)

        return p


def renice(pid, value):
    if os.name != "nt" and value:
        try:
            Popen(["renice", str(value), str(pid)], stdout=PIPE, stderr=PIPE, bufsize=-1)
        except:
            print "Renice failed"
