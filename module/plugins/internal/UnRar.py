# -*- coding: utf-8 -*-

import os
import re
import string
import subprocess

from module.plugins.internal.Extractor import Extractor, ArchiveError, CRCError, PasswordError
from module.plugins.internal.misc import decode, encode, fsjoin, renice


class UnRar(Extractor):
    __name__    = "UnRar"
    __type__    = "extractor"
    __version__ = "1.31"
    __status__  = "testing"

    __description__ = """RAR extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("Immenz"        , "immenz@gmx.net"   )]


    CMD        = "unrar"
    EXTENSIONS = ["rar", "zip", "cab", "arj", "lzh", "tar", "gz", "ace", "uue",
                  "bz2", "jar", "iso", "7z", "xz", "z"]

    _RE_PART    = re.compile(r'\.(part|r)\d+(\.rar|\.rev)?(\.bad)?', re.I)
    _RE_FIXNAME = re.compile(r'Building (.+)')
    _RE_FILES   = re.compile(r'^(.)(\s*[\w\-.]+)\s+(\d+\s+)+(?:\d+\%\s+)?[\d\-]{8}\s+[\d\:]{5}', re.I | re.M)
    _RE_BADPWD  = re.compile(r'password', re.I)
    _RE_BADCRC  = re.compile(r'encrypted|damaged|CRC failed|checksum error|corrupt', re.I)
    _RE_VERSION = re.compile(r'(?:UN)?RAR\s(\d+\.\d+)', re.I)


    @classmethod
    def find(cls):
        try:
            if os.name == "nt":
                cls.CMD = os.path.join(pypath, "RAR.exe")
            else:
                cls.CMD = "rar"

            p = subprocess.Popen([cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            # cls.__name__ = "RAR"
            cls.REPAIR = True

        except OSError:
            try:
                if os.name == "nt":
                    cls.CMD = os.path.join(pypath, "UnRAR.exe")
                else:
                    cls.CMD = "unrar"

                p = subprocess.Popen([cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()

            except OSError:
                return False

        m = cls._RE_VERSION.search(out)
        if m is not None:
            cls.VERSION = m.group(1)

        return True


    @classmethod
    def ismultipart(cls, filename):
        return True if cls._RE_PART.search(filename) else False


    def verify(self, password=None):
        p = self.call_cmd("l", "-v", self.target, password=password)
        out, err = p.communicate()

        if self._RE_BADPWD.search(err):
            raise PasswordError

        if self._RE_BADCRC.search(err):
            raise CRCError(err)

        #: Output only used to check if passworded files are present
        for attr in self._RE_FILES.findall(out):
            if attr[0].startswith("*"):
                raise PasswordError


    def repair(self):
        p = self.call_cmd("rc", self.target)

        #: Communicate and retrieve stderr
        self.progress(p)
        err = p.stderr.read().strip()

        if err or p.returncode:
            p = self.call_cmd("r", self.target)

            # communicate and retrieve stderr
            self.progress(p)
            err = p.stderr.read().strip()

            if err or p.returncode:
                return False

            else:
                dir  = os.path.dirname(filename)
                name = _RE_FIXNAME.search(out).group(1)

                self.filename = os.path.join(dir, name)

        return True


    def progress(self, process):
        s = ""
        while True:
            c = process.stdout.read(1)
            #: Quit loop on eof
            if not c:
                break
            #: Reading a percentage sign -> set progress and restart
            if c == "%":
                self.notifyprogress(int(s))
                s = ""
            #: Not reading a digit -> therefore restart
            elif c not in string.digits:
                s = ""
            #: Add digit to progressstring
            else:
                s += c


    def extract(self, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_cmd(command, self.target, self.dest, password=password)

        #: Communicate and retrieve stderr
        self.progress(p)
        err = p.stderr.read().strip()

        if err:
            if self._RE_BADPWD.search(err):
                raise PasswordError

            elif self._RE_BADCRC.search(err):
                raise CRCError(err)

            else:  #: Raise error if anything is on stderr
                raise ArchiveError(err)

        if p.returncode:
            raise ArchiveError(_("Process return code: %d") % p.returncode)


    def chunks(self):
        dir, name = os.path.split(self.filename)

        #: Actually extracted file
        files = [self.filename]

        #: eventually Multipart Files
        files.extend(fsjoin(dir, os.path.basename(file)) for file in filter(self.ismultipart, os.listdir(dir))
                     if re.sub(self._RE_PART, "", name) == re.sub(self._RE_PART, "", file))

        return files


    def list(self, password=None):
        command = "vb" if self.fullpath else "lb"

        p = self.call_cmd(command, "-v", self.target, password=password)
        out, err = p.communicate()

        if "Cannot open" in err:
            raise ArchiveError(_("Cannot open file"))

        if err.strip():  #: Only log error at this point
            self.log_error(err.strip())

        result = set()
        if not self.fullpath and self.VERSION.startswith('5'):
            #@NOTE: Unrar 5 always list full path
            for f in decode(out).splitlines():
                f = fsjoin(self.dest, os.path.basename(f.strip()))
                if os.path.isfile(f):
                    result.add(fsjoin(self.dest, os.path.basename(f)))
        else:
            for f in decode(out).splitlines():
                result.add(fsjoin(self.dest, f.strip()))

        return list(result)


    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        #: Overwrite flag
        if self.overwrite:
            args.append("-o+")
        else:
            args.append("-o-")
            args.append("-or")

        for word in self.excludefiles:
            args.append("-x'%s'" % word.strip())

        #: Assume yes on all queries
        args.append("-y")

        #: Set a password
        password = kwargs.get('password')

        if password:
            args.append("-p%s" % password)
        else:
            args.append("-p-")

        if self.keepbroken:
            args.append("-kb")

        #@NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [self.CMD, command] + args + list(xargs)
        self.log_debug("EXECUTE " + " ".join(call))

        call = map(encode, call)
        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        renice(p.pid, self.priority)

        return p
