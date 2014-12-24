# -*- coding: utf-8 -*-

import os
import re

from glob import glob
from os.path import basename, dirname, join
from string import digits
from subprocess import Popen, PIPE

from module.plugins.internal.AbstractExtractor import AbtractExtractor, PasswordError, ArchiveError, CRCError
from module.utils import save_join, decode


def renice(pid, value):
    if os.name != "nt" and value:
        try:
            Popen(["renice", str(value), str(pid)], stdout=PIPE, stderr=PIPE, bufsize=-1)
        except:
            print "Renice failed"


class UnRar(AbtractExtractor):
    __name__    = "UnRar"
    __version__ = "1.00"

    __description__ = """Rar extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    CMD = "unrar"

    EXTENSIONS = ["rar", "zip", "cab", "arj", "lzh", "tar", "gz", "bz2", "ace", "uue", "jar", "iso", "7z", "xz", "z"]


    #@NOTE: there are some more uncovered rar formats
    re_rarpart = re.compile(r'(.*)\.part(\d+)\.rar$', re.I)
    re_rarfile = re.compile(r'.*\.(rar|r\d+)$', re.I)

    re_filelist  = re.compile(r'(.+)\s+(\d+)\s+(\d+)\s+|(.+)\s+(\d+)\s+\d\d-\d\d-\d\d\s+\d\d:\d\d\s+(.+)')
    re_wrongpwd  = re.compile(r'password', re.I)
    re_wrongcrc  = re.compile(r'encrypted|damaged|CRC failed|checksum error', re.I)


    @classmethod
    def checkDeps(cls):
        if os.name == "nt":
            cls.CMD = join(pypath, "UnRAR.exe")
            p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
            p.communicate()
        else:
            try:
                p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
                p.communicate()

            except OSError:
                # fallback to rar
                cls.CMD = "rar"
                p = Popen([cls.CMD], stdout=PIPE, stderr=PIPE)
                p.communicate()

        return True


    @classmethod
    def isArchive(cls, file):
        f = basename(file).lower()
        return any(f.endswith('.%s' % ext) for ext in cls.EXTENSIONS)


    @classmethod
    def getTargets(cls, files_ids):
        targets = []

        for file, id in files_ids:
            if not cls.isArchive(file):
                continue

            m = cls.re_rarpart.findall(file)
            if m:
                # only add first parts
                if int(m[0][1]) == 1:
                    targets.append((file, id))
            else:
                targets.append((file, id))

        return targets


    def check(self, out="", err=""):
        if not out or not err:
            return

        if err.strip():
            if self.re_wrongpwd.search(err):
                raise PasswordError

            elif self.re_wrongcrc.search(err):
                raise CRCError

            else:  #: raise error if anything is on stderr
                raise ArchiveError(err.strip())

        # output only used to check if passworded files are present
        for attr in self.re_filelist.findall(out):
            if attr[0].startswith("*"):
                raise PasswordError


    def verify(self):
        p = self.call_cmd("l", "-v", self.file, password=self.password)

        self.check(*p.communicate())

        if p and p.returncode:
            raise ArchiveError("Process terminated")

        if not self.list():
            raise ArchiveError("Empty archive")


    def isPassword(self, password):
        if isinstance(password, basestring):
            p = self.call_cmd("l", "-v", self.file, password=password)
            out, err = p.communicate()

            if not self.re_wrongpwd.search(err):
                return True

        return False


    def repair(self):
        p = self.call_cmd("rc", self.file)
        out, err = p.communicate()

        if p.returncode or err.strip():
            p = self.call_cmd("r", self.file)
            out, err = p.communicate()

            if p.returncode or err.strip():
                return False
            else:
                self.file = join(dirname(self.file), re.search(r'(fixed|rebuild)\.%s' % basename(self.file), out).group(0))

        return True


    def extract(self, progress=lambda x: None):
        self.verify()

        progress(0)

        command = "x" if self.fullpath else "e"

        p = self.call_cmd(command, self.file, self.out, password=self.password)

        renice(p.pid, self.renice)

        progressstring = ""
        while True:
            c = p.stdout.read(1)
            # quit loop on eof
            if not c:
                break
            # reading a percentage sign -> set progress and restart
            if c is '%':
                progress(int(progressstring))
                progressstring = ""
            # not reading a digit -> therefore restart
            elif c not in digits:
                progressstring = ""
            # add digit to progressstring
            else:
                progressstring += c

        progress(100)

        self.files = self.list()

        # retrieve stderr
        self.check(err=p.stderr.read())

        if p.returncode:
            raise ArchiveError("Process terminated")


    def getDeleteFiles(self):
        if ".part" in basename(self.file):
            return glob(re.sub("(?<=\.part)([01]+)", "*", self.file, re.I))

        # get files which matches .r* and filter unsuited files out
        parts = glob(re.sub(r"(?<=\.r)ar$", "*", self.file, re.I))

        return filter(lambda x: self.re_rarfile.match(x), parts)


    def list(self):
        command = "vb" if self.fullpath else "lb"

        p = self.call_cmd(command, "-v", self.file, password=self.password)
        out, err = p.communicate()

        if err.strip():
            self.m.logError(err)
            if "Cannot open" in err:
                return list()

        if p.returncode:
            self.m.logError("Process terminated")
            return list()

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
            args.append("-x%s" % word.strip())

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
        self.m.logDebug(" ".join(call))

        return Popen(call, stdout=PIPE, stderr=PIPE)
