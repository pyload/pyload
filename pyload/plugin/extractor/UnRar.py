# -*- coding: utf-8 -*-

import os
import re

from glob import glob
from string import digits
from subprocess import Popen, PIPE

from pyload.plugin.Extractor import Extractor, ArchiveError, CRCError, PasswordError
from pyload.utils import decode, fs_encode, fs_join


def renice(pid, value):
    if value and os.name != "nt":
        try:
            Popen(["renice", str(value), str(pid)], stdout=PIPE, stderr=PIPE, bufsize=-1)

        except Exception:
            pass


class UnRar(Extractor):
    __name    = "UnRar"
    __type    = "extractor"
    __version = "1.14"

    __description = """Rar extractor plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("Immenz", "immenz@gmx.net"),]


    CMD = "unrar"
    VERSION = ""
    EXTENSIONS = [".rar"]


    re_multipart = re.compile(r'\.(part|r)(\d+)(?:\.rar)?(\.rev|\.bad)?',re.I)

    re_filefixed = re.compile(r'Building (.+)')
    re_filelist  = re.compile(r'^(.)(\s*[\w\.\-]+)\s+(\d+\s+)+(?:\d+\%\s+)?[\d\-]{8}\s+[\d\:]{5}', re.M|re.I)

    re_wrongpwd  = re.compile(r'password', re.I)
    re_wrongcrc  = re.compile(r'encrypted|damaged|CRC failed|checksum error|corrupt', re.I)

    re_version   = re.compile(r'(?:UN)?RAR\s(\d+\.\d+)', re.I)


    @classmethod
    def isUsable(cls):
        if os.name == "nt":
            try:
                cls.CMD = os.path.join(pypath, "RAR.exe")
                p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                cls.__name__ = "RAR"
                cls.REPAIR = True
            except OSError:
                cls.CMD = os.path.join(pypath, "UnRAR.exe")
                p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
        else:
            try:
                p = Popen(["rar"], stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                cls.__name__ = "RAR"
                cls.REPAIR = True
            except OSError:  #: fallback to unrar
                p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()

        cls.VERSION = cls.re_version.search(out).group(1)

        return True


    @classmethod
    def isMultipart(cls,filename):
        multipart = cls.re_multipart.search(filename)
        if multipart:
            # First Multipart file (part1.rar for *.part1-9.rar format or *.rar for .r1-9 format) handled as normal Archive
            return False if (multipart.group(1) == "part" and int(multipart.group(2)) == 1 and not multipart.group(3)) else True

        return False


    def test(self, password):
        p = self.call_cmd("t", "-v", fs_encode(self.filename), password=password)
        self._progress(p)
        err = p.stderr.read().strip()

        if self.re_wrongpwd.search(err):
            raise PasswordError

        if self.re_wrongcrc.search(err):
            raise CRCError(err)


    def check(self, password):
        p = self.call_cmd("l", "-v", fs_encode(self.filename), password=password)
        out, err = p.communicate()

        if self.re_wrongpwd.search(err):
            raise PasswordError

        if self.re_wrongcrc.search(err):
            raise CRCError(err)

        # output only used to check if passworded files are present
        for attr in self.re_filelist.findall(out):
            if attr[0].startswith("*"):
                raise PasswordError


    def repair(self):
        p = self.call_cmd("rc", fs_encode(self.filename))

        # communicate and retrieve stderr
        self._progress(p)
        err = p.stderr.read().strip()
        if err or p.returncode:
            return False
        return True


    def _progress(self, process):
        s = ""
        while True:
            c = process.stdout.read(1)
            # quit loop on eof
            if not c:
                break
            # reading a percentage sign -> set progress and restart
            if c == '%':
                self.notifyProgress(int(s))
                s = ""
            # not reading a digit -> therefore restart
            elif c not in digits:
                s = ""
            # add digit to progressstring
            else:
                s += c


    def extract(self, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_cmd(command, fs_encode(self.filename), self.out, password=password)

        renice(p.pid, self.renice)

        # communicate and retrieve stderr
        self._progress(p)
        err = p.stderr.read().strip()

        if err:
            if self.re_wrongpwd.search(err):
                raise PasswordError

            elif self.re_wrongcrc.search(err):
                raise CRCError(err)

            else:  #: raise error if anything is on stderr
                raise ArchiveError(err)

        if p.returncode:
            raise ArchiveError(_("Process return code: %d") % p.returncode)

        self.files = self.list(password)


    def getDeleteFiles(self):
        dir, name = os.path.split(self.filename)

        # actually extracted file
        files = [self.filename]

        # eventually Multipart Files
        files.extend(fs_join(dir, os.path.basename(file)) for file in filter(self.isMultipart, os.listdir(dir))
                     if re.sub(self.re_multipart,".rar",name) == re.sub(self.re_multipart,".rar",file))

        return files


    def list(self, password=None):
        command = "vb" if self.fullpath else "lb"

        p = self.call_cmd(command, "-v", fs_encode(self.filename), password=password)
        out, err = p.communicate()

        if "Cannot open" in err:
            raise ArchiveError(_("Cannot open file"))

        if err.strip():  #: only log error at this point
            self.manager.logError(err.strip())

        result = set()
        if not self.fullpath and self.VERSION.startswith('5'):
            # NOTE: Unrar 5 always list full path
            for f in decode(out).splitlines():
                f = fs_join(self.out, os.path.basename(f.strip()))
                if os.path.isfile(f):
                    result.add(fs_join(self.out, os.path.basename(f)))
        else:
            for f in decode(out).splitlines():
                f = f.strip()
                result.add(fs_join(self.out, f))

        return list(result)


    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        # overwrite flag
        if self.overwrite:
            args.append("-o+")
        else:
            args.append("-o-")
            if self.delete:
                args.append("-or")

        for word in self.excludefiles:
            args.append("-x'%s'" % word.strip())

        # assume yes on all queries
        args.append("-y")

        # set a password
        if "password" in kwargs and kwargs['password']:
            args.append("-p%s" % kwargs['password'])
        else:
            args.append("-p-")

        if self.keepbroken:
            args.append("-kb")

        # NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [self.CMD, command] + args + list(xargs)

        self.manager.logDebug(" ".join(call))

        p = Popen(call, stdout=PIPE, stderr=PIPE)
        return p
