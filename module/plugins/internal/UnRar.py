# -*- coding: utf-8 -*-

import os
import re

from glob import glob
from os.path import join
from string import digits
from subprocess import Popen, PIPE

from module.plugins.internal.AbstractExtractor import AbtractExtractor, WrongPassword, ArchiveError, CRCError
from module.utils import save_join, decode


class UnRar(AbtractExtractor):
    __name__ = "UnRar"
    __version__ = "0.16"

    __description__ = """Rar extractor plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"

    CMD = "unrar"

    # there are some more uncovered rar formats
    re_version = re.compile(r"(UNRAR 5[\.\d]+(.*?)freeware)")
    re_splitfile = re.compile(r"(.*)\.part(\d+)\.rar$", re.I)
    re_partfiles = re.compile(r".*\.(rar|r[0-9]+)", re.I)
    re_filelist = re.compile(r"(.+)\s+(\d+)\s+(\d+)\s+")
    re_filelist5 = re.compile(r"(.+)\s+(\d+)\s+\d\d-\d\d-\d\d\s+\d\d:\d\d\s+(.+)")
    re_wrongpwd = re.compile("(Corrupt file or wrong password|password incorrect)", re.I)


    @staticmethod
    def checkDeps():
        if os.name == "nt":
            UnRar.CMD = join(pypath, "UnRAR.exe")
            p = Popen([UnRar.CMD], stdout=PIPE, stderr=PIPE)
            p.communicate()
        else:
            try:
                p = Popen([UnRar.CMD], stdout=PIPE, stderr=PIPE)
                p.communicate()
            except OSError:

                # fallback to rar
                UnRar.CMD = "rar"
                p = Popen([UnRar.CMD], stdout=PIPE, stderr=PIPE)
                p.communicate()

        return True

    @staticmethod
    def getTargets(files_ids):
        result = []

        for file, id in files_ids:
            if not file.endswith(".rar"):
                continue

            match = UnRar.re_splitfile.findall(file)
            if match:
                # only add first parts
                if int(match[0][1]) == 1:
                    result.append((file, id))
            else:
                result.append((file, id))

        return result

    def init(self):
        self.passwordProtected = False
        self.headerProtected = False  #: list files will not work without password
        self.smallestFile = None  #: small file to test passwords
        self.password = ""  #: save the correct password

    def checkArchive(self):
        p = self.call_unrar("l", "-v", self.file)
        out, err = p.communicate()
        if self.re_wrongpwd.search(err):
            self.passwordProtected = True
            self.headerProtected = True
            return True

        # output only used to check if passworded files are present
        if self.re_version.search(out):
            for attr, size, name in self.re_filelist5.findall(out):
                if attr.startswith("*"):
                    self.passwordProtected = True
                    return True
        else:
            for name, size, packed in self.re_filelist.findall(out):
                if name.startswith("*"):
                    self.passwordProtected = True
                    return True

        self.listContent()
        if not self.files:
            raise ArchiveError("Empty Archive")

        return False

    def checkPassword(self, password):
        # at this point we can only verify header protected files
        if self.headerProtected:
            p = self.call_unrar("l", "-v", self.file, password=password)
            out, err = p.communicate()
            if self.re_wrongpwd.search(err):
                return False

        return True

    def extract(self, progress, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_unrar(command, self.file, self.out, password=password)
        renice(p.pid, self.renice)

        progress(0)
        progressstring = ""
        while True:
            c = p.stdout.read(1)
            # quit loop on eof
            if not c:
                break
            # reading a percentage sign -> set progress and restart
            if c == '%':
                progress(int(progressstring))
                progressstring = ""
            # not reading a digit -> therefore restart
            elif c not in digits:
                progressstring = ""
            # add digit to progressstring
            else:
                progressstring = progressstring + c
        progress(100)

        # retrieve stderr
        err = p.stderr.read()

        if "CRC failed" in err and not password and not self.passwordProtected:
            raise CRCError
        elif "CRC failed" in err:
            raise WrongPassword
        if err.strip():  #: raise error if anything is on stderr
            raise ArchiveError(err.strip())
        if p.returncode:
            raise ArchiveError("Process terminated")

        if not self.files:
            self.password = password
            self.listContent()

    def getDeleteFiles(self):
        if ".part" in self.file:
            return glob(re.sub("(?<=\.part)([01]+)", "*", self.file, re.IGNORECASE))
        # get files which matches .r* and filter unsuited files out
        parts = glob(re.sub(r"(?<=\.r)ar$", "*", self.file, re.IGNORECASE))
        return filter(lambda x: self.re_partfiles.match(x), parts)

    def listContent(self):
        command = "vb" if self.fullpath else "lb"
        p = self.call_unrar(command, "-v", self.file, password=self.password)
        out, err = p.communicate()

        if "Cannot open" in err:
            raise ArchiveError("Cannot open file")

        if err.strip():  #: only log error at this point
            self.m.logError(err.strip())

        result = set()

        for f in decode(out).splitlines():
            f = f.strip()
            result.add(save_join(self.out, f))

        self.files = result

    def call_unrar(self, command, *xargs, **kwargs):
        args = []
        # overwrite flag
        args.append("-o+") if self.overwrite else args.append("-o-")

        if self.excludefiles:
            for word in self.excludefiles.split(';'):
                args.append("-x%s" % word)

        # assume yes on all queries
        args.append("-y")

        # set a password
        if "password" in kwargs and kwargs['password']:
            args.append("-p%s" % kwargs['password'])
        else:
            args.append("-p-")

        # NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [self.CMD, command] + args + list(xargs)
        self.m.logDebug(" ".join(call))

        p = Popen(call, stdout=PIPE, stderr=PIPE)

        return p


def renice(pid, value):
    if os.name != "nt" and value:
        try:
            Popen(["renice", str(value), str(pid)], stdout=PIPE, stderr=PIPE, bufsize=-1)
        except:
            print "Renice failed"
