# -*- coding: utf-8 -*-

import os
import re

from glob import glob
from string import digits
from subprocess import Popen, PIPE

from module.plugins.internal.Extractor import Extractor, ArchiveError, CRCError, PasswordError
from module.utils import decode, fs_encode, save_join


def renice(pid, value):
    if value and os.name != "nt":
        try:
            Popen(["renice", str(value), str(pid)], stdout=PIPE, stderr=PIPE, bufsize=-1)

        except Exception:
            pass


class UnRar(Extractor):
    __name__    = "UnRar"
    __version__ = "1.10"

    __description__ = """Rar extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    CMD = "unrar"

    # TODO: Find out what Filetypes Unrar supports exactly
    EXTENSIONS = [".rar", ".cab", ".arj", ".lzh", ".tar", ".gz", ".bz2",
                  ".ace", ".uue", ".jar", ".iso", ".7z", ".xz", ".z"]

    #@NOTE: there are some more uncovered rar formats
    re_rarpart1 = re.compile(r'\.part(\d+)\.rar$', re.I)
    re_rarpart2 = re.compile(r'\.r(\d+)$', re.I)

    re_filefixed = re.compile(r'Building (.+)')
    re_filelist  = re.compile(r'(.+)\s+(\D+)\s+(\d+)\s+\d\d-\d\d-\d\d\s+\d\d:\d\d\s+(.+)')

    re_wrongpwd  = re.compile(r'password', re.I)
    re_wrongcrc  = re.compile(r'encrypted|damaged|CRC failed|checksum error', re.I)


    @classmethod
    def isUsable(cls):
        if os.name == "nt":
            cls.CMD = os.path.join(pypath, "UnRAR.exe")
            p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
            p.communicate()
        else:
            try:
                p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
                p.communicate()

            except OSError:  #: fallback to rar
                cls.CMD = "rar"
                p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
                p.communicate()

        return True


    def check(self):
        p = self.call_cmd("l", "-v", fs_encode(self.filename))
        out, err = p.communicate()

        if self.re_wrongpwd.search(err):
            raise PasswordError

        if self.re_wrongcrc.search(err):
            raise CRCError(err)

        # output only used to check if passworded files are present
        for attr in self.re_filelist.findall(out):
            if attr[0].startswith("*"):
                raise PasswordError


    def isPassword(self, password):
        # at this point we can only verify header protected files
        p = self.call_cmd("l", "-v", fs_encode(self.filename), password=password)
        out, err = p.communicate()
        return False if self.re_wrongpwd.search(err) else True


    def repair(self):
        p = self.call_cmd("rc", fs_encode(self.filename))

        # communicate and retrieve stderr
        self._progress(p)
        err = p.stderr.read().strip()

        if err or p.returncode:
            p = self.call_cmd("r", fs_encode(self.filename))

            # communicate and retrieve stderr
            self._progress(p)
            err = p.stderr.read().strip()

            if err or p.returncode:
                return False
            else:
                dir  = os.path.dirname(filename)
                name = re_filefixed.search(out).group(1)

                self.filename = os.path.join(dir, name)

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
        files = []

        for i in (1, 2):
            try:
                dir, name = os.path.split(self.filename)

                part     = getattr(self, "re_rarpart%d" % i).search(name).group(1)
                new_name = name[::-1].replace((".part%s.rar" % part)[::-1], ".part*.rar"[::-1], 1)[::-1]
                file     = fs_encode(os.path.join(dir, new_name))

                files.extend(glob(file))

            except Exception:
                continue

        if self.filename not in files:
            files.insert(0, self.filename)

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
        for f in decode(out).splitlines():
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
