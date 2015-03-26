# -*- coding: utf-8 -*-

import os
import re
import subprocess

from glob import glob
from string import digits

from module.plugins.internal.Extractor import Extractor, ArchiveError, CRCError, PasswordError
from module.utils import fs_decode, fs_encode, save_join


def renice(pid, value):
    if value and os.name != "nt":
        try:
            subprocess.Popen(["renice", str(value), str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)

        except Exception:
            pass


class UnRar(Extractor):
    __name__    = "UnRar"
    __version__ = "1.20"

    __description__ = """Rar extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("Immenz"        , "immenz@gmx.net"   )]


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
                p = subprocess.Popen([cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                cls.__name__ = "RAR"
                cls.REPAIR = True

            except OSError:
                cls.CMD = os.path.join(pypath, "UnRAR.exe")
                p = subprocess.Popen([cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
        else:
            try:
                p = subprocess.Popen(["rar"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                cls.__name__ = "RAR"
                cls.REPAIR = True

            except OSError:  #: fallback to unrar
                p = subprocess.Popen([cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()

        m = cls.re_version.search(out)
        cls.VERSION = m.group(1) if m else '(version unknown)'

        return True


    @classmethod
    def isMultipart(cls, filename):
        return True if cls.re_multipart.search(filename) else False


    def verify(self, password):
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
        files.extend(save_join(dir, os.path.basename(file)) for file in filter(self.isMultipart, os.listdir(dir))
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
            for f in fs_decode(out).splitlines():
                f = save_join(self.out, os.path.basename(f.strip()))
                if os.path.isfile(f):
                    result.add(save_join(self.out, os.path.basename(f)))
        else:
            for f in fs_decode(out).splitlines():
                f = f.strip()
                result.add(save_join(self.out, f))

        return list(result)


    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        # overwrite flag
        if self.overwrite:
            args.append("-o+")
        else:
            args.append("-o-")
            if self.delete != 'No':
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

        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p
