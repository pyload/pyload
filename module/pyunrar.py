#!/usr/bin/env python
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
    
    @author: mkaay <mkaay@mkaay.de>
"""

from subprocess import Popen, PIPE
import re
from time import sleep
from tempfile import mkdtemp
from shutil import rmtree, move
from shutil import Error as FileError
from os.path import join, abspath, basename, dirname
from os import remove, makedirs

EXITMAP = {
    255: ("USER BREAK 	User stopped the process"),
    9: ("CREATE ERROR", "Create file error"),
    8: ("MEMORY ERROR", "Not enough memory for operation"),
    7: ("USER ERROR", "Command line option error"),
    6: ("OPEN ERROR", "Open file error"),
    5: ("WRITE ERROR", "Write to disk error"),
    4: ("LOCKED ARCHIVE", "Attempt to modify an archive previously locked by the 'k' command"),
    3: ("CRC ERROR", "A CRC error occurred when unpacking"),
    2: ("FATAL ERROR", "A fatal error occurred"),
    1: ("WARNING", "Non fatal error(s) occurred"),
    0: ("SUCCESS", "Successful operation (User exit)"),
}

class UnknownError(Exception):
    pass

class NoFilesError(Exception):
    pass

class WrongPasswordError(Exception):
    pass

class CommandError(Exception):
    def __init__(self, ret=None, stdout=None, stderr=None):
        self.ret = ret
        self.stdout = stdout
        self.stderr = stderr
    
    def __str__(self):
        return "%s %s %s" % (EXITMAP[self.ret], self.stdout, self.stderr)
    
    def __repr__(self):
        try:
            return "<CommandError %s (%s)>" % (EXITMAP[self.ret][0], EXITMAP[self.ret][1])
        except:
            return "<CommandError>"
    
    def getExitCode(self):
        return self.ret
    
    def getMappedExitCode(self):
        return EXITMAP[self.ret]

class Unrar():
    def __init__(self, archive):
        """
            archive should be be first or only part
        """
        self.archive = archive
        self.pattern = None
        m = re.match("^(.*).part(\d+).rar$", archive)
        if m:
            self.pattern = "%s.part*.rar" % m.group(1)
        else: #old style
            self.pattern = "%s.r*" % archive.replace(".rar", "")
        self.cmd = "unrar"
        self.encrypted = None
        self.headerEncrypted = None
        self.smallestFiles = None
        self.password = None
    
    def listContent(self, password=None):
        """
            returns a list with all infos to the files in the archive
            dict keys: name, version, method, crc, attributes, time, date, ratio, size_packed, size
            @return list(dict, dict, ...)
        """
        f = self.archive
        if self.pattern:
            f = self.pattern
        args = [self.cmd, "v"]
        if password:
            args.append("-p%s" % password)
        else:
            args.append("-p-")
        args.append(f)
        p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        ret = p.wait()
        if ret == 3:
            self.headerEncrypted = True
            raise WrongPasswordError()
        elif ret == 0 and password:
            self.headerEncrypted = False
        o = p.stdout.read()
        inList = False
        infos = {}
        nameLine = False
        name = ""
        for line in o.split("\n"):
            if line == "-"*79:
                inList = not inList
                continue
            if inList:
                nameLine = not nameLine
                if nameLine:
                    name = line
                    if name[0] == "*": #check for pw indicator
                        name = name[1:]
                        self.encrypted = True
                    name = name.strip()
                    continue
                s = line.split(" ")
                s = [e for e in s if e]
                s.reverse()
                d = {}
                for k, v in zip(["version", "method", "crc", "attributes", "time", "date", "ratio", "size_packed", "size"], s[0:9]):
                    d[k] = v
                #if d["crc"] == "00000000" and len(d["method"]) == 2:
                if re.search("d", d["attributes"].lower()): #directory
                    continue
                d["name"] = name
                d["size_packed"] = int(d["size_packed"])
                d["size"] = int(d["size"])
                if infos.has_key(name):
                    infos[name]["size_packed"] = infos[name]["size_packed"] + d["size_packed"]
                    infos[name]["crc"].append(d["crc"])
                else:
                    infos[name] = d
                    infos[name]["crc"] = [d["crc"]]
        infos = infos.values()
        return infos
    
    def listSimple(self, password=None):
        """
            return a list with full path to all files
            @return list
        """
        l = self.listContent(password=password)
        return [e["name"] for e in l]
    
    def getSmallestFile(self, password=None):
        """
            return the file info for the smallest file
            @return dict
        """
        files = self.listContent(password=password)
        smallest = (-1, -1)
        for i, f in enumerate(files):
            if f["size"] < smallest[1] or smallest[1] == -1:
                smallest = (i, f["size"])
        if smallest[0] == -1:
            raise UnknownError()
        self.smallestFiles = files[smallest[0]]
        return files[smallest[0]]
    
    def needPassword(self):
        """
            do we need a password?
            @return bool
        """
        if not self.smallestFiles:
            try:
                self.getSmallestFile()
            except WrongPasswordError:
                return True
        return self.headerEncrypted or self.encrypted
    
    def checkPassword(self, password, statusFunction=None):
        """
            check if password is okay
            @return bool
        """
        if not self.needPassword():
            return True
        f = self.archive
        if self.pattern:
            f = self.pattern
        args = [self.cmd, "t", "-p%s" % password, f]
        try:
            args.append(self.getSmallestFile(password)["name"])
        except WrongPasswordError:
            return False
        p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (ret, out) = self.processOutput(p, statusFunction)
        if ret == 3:
            raise False
        elif ret == 0:
            return True
        else:
            raise UnknownError()
    
    def extract(self, password=None, fullPath=True, files=[], exclude=[], destination=None, overwrite=False, statusFunction=None):
        """
            extract the archive
            @return bool: extract okay?
            raises WrongPasswordError or CommandError
        """
        f = self.archive
        if self.pattern:
            f = self.pattern
        args = [self.cmd]
        if fullPath:
            args.append("x")
        else:
            args.append("e")
        if not password:
            password = "-"
        if overwrite:
            args.append("-o+")
        else:
            args.append("-o-")
        args.append("-p%s" % password)
        args.append(f)
        if files:
            args.extend([e for e in files])
        if exclude:
            args.extend(["-x%s" % e for e in exclude])
        if destination:
            args.append(destination)
        p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (ret, out) = self.processOutput(p, statusFunction)
        if ret == 3:
            raise WrongPasswordError()
        elif ret == 0:
            return True
        else:
            raise CommandError(ret=ret, stdout=out, stderr=p.stderr.read())
    
    def crackPassword(self, passwords=[], fullPath=True, destination=None, overwrite=False, statusFunction=None, exclude=[]):
        """
            check password list until the right one is found and extract the archive
            @return bool: password found?
        """
        correctPassword = None
        if self.needPassword():
            for password in passwords:
                sf = []
                try:
                    sf.append(self.getSmallestFile(password)["name"])
                except WrongPasswordError:
                    continue
                tdir = mkdtemp(prefix="rar")
                try:
                    self.extract(password=password, fullPath=fullPath, destination=tdir, overwrite=overwrite, statusFunction=statusFunction, files=sf)
                except WrongPasswordError:
                    continue
                else:
                    if not destination:
                        destination = "."
                    if overwrite:
                        try:
                            remove(abspath(join(destination, sf[0])))
                        except OSError, e:
                            if not e.errno == 2:
                                raise e
                    f = sf[0]
                    d = destination
                    if fullPath:
                        try:
                            makedirs(dirname(join(abspath(destination), sf[0])))
                        except OSError, e:
                            if not e.errno == 17:
                                raise e
                        d = join(destination, dirname(f))
                    else:
                        f = basename(f)
                    try:
                        move(join(tdir, f), abspath(d))
                    except FileError:
                        pass
                    exclude.append(sf[0])
                    correctPassword = password
                    break
                finally:
                    rmtree(tdir)
                    pass
        try:
            self.extract(password=correctPassword, fullPath=fullPath, destination=destination, overwrite=overwrite, statusFunction=statusFunction, exclude=exclude)
            self.password = correctPassword
            return True
        except WrongPasswordError:
            return False
    
    def processOutput(self, p, statusFunction=None):
        """
            internal method
            parse the progress output of the rar/unrar command
            @return int: exitcode
                    string: command output
        """
        ret = None
        out = ""
        tmp = None
        count = 0
        perc = 0
        tperc = "0"
        last = None
        digits = "1 2 3 4 5 6 7 8 9 0".split(" ")
        if not statusFunction:
            statusFunction = lambda p: None
        statusFunction(0)
        while ret == None or tmp:
            tmp = p.stdout.read(1)
            if tmp:
                out += tmp
                if tmp == chr(8):
                    if last == tmp:
                        count += 1
                        tperc = "0"
                    else:
                        count = 0
                        if perc < int(tperc):
                            perc = int(tperc)
                            statusFunction(perc)
                elif count >= 3:
                    if tmp == "\n":
                        count = 0
                    elif tmp in digits:
                        tperc += tmp
                last = tmp
            else:
                sleep(0.01)
            ret = p.poll()
        statusFunction(100)
        return ret, out
    
    def getPassword(self):
        """
            return the correct password
            works only in conjunction with 'crackPassword'
            @return string: password
        """
        return self.password

if __name__ == "__main__":
    from pprint import pprint
    u = Unrar("archive.part1.rar", multi=True)
    u = Unrar("parchive.part1.rar", multi=True)
    pprint(u.listContent())
    u = Unrar("pharchive.part1.rar", multi=True)
    pprint(u.listContent(password="test"))
    u = Unrar("bigarchive.rar")
    pprint(u.listContent())
    print u.getSmallestFile()
    try:
        def s(p):
            print p
        print u.crackPassword(passwords=["test1", "ggfd", "423r", "test"], destination=".", statusFunction=s, overwrite=True)
    except CommandError, e:
        print e
