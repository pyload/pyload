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
    __version__ = "1.06"

    __description__ = """Rar extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    CMD = "unrar"

    EXTENSIONS = [".rar", ".zip", ".cab", ".arj", ".lzh", ".tar", ".gz", ".bz2",
                  ".ace", ".uue", ".jar", ".iso", ".7z", ".xz", ".z"]

    #@NOTE: there are some more uncovered rar formats
    re_rarpart1 = re.compile(r'\.part(\d+)\.rar$', re.I)
    re_rarpart2 = re.compile(r'\.r(\d+)$', re.I)

    re_filelist  = re.compile(r'(.+)\s+(\d+)\s+(\d+)\s+|(.+)\s+(\d+)\s+\d\d-\d\d-\d\d\s+\d\d:\d\d\s+(.+)')
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


    @classmethod
    def getTargets(cls, files_ids):
        targets = []

        for fname, id in files_ids:
            if not cls.isArchive(fname):
                continue

            m = cls.re_rarpart1.search(fname)
            if not m or int(m.group(1)) == 1:  #@NOTE: only add first part file
                targets.append((fname, id))

        return targets


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
        out, err = p.communicate()

        if p.returncode or err.strip():
            p = self.call_cmd("r", fs_encode(self.filename))
            out, err = p.communicate()

            if p.returncode or err.strip():
                return False
            else:
                dir, name = os.path.split(filename)

                if 'fixed' in out:
                    self.filename = os.path.join(dir, 'fixed.' + name)

                elif 'rebuild' in out:
                    self.filename = os.path.join(dir, 'rebuild.' + name)

        return True


    def extract(self, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_cmd(command, fs_encode(self.filename), self.out, password=password)

        renice(p.pid, self.renice)

        progressstring = ""
        while True:
            c = p.stdout.read(1)
            # quit loop on eof
            if not c:
                break
            # reading a percentage sign -> set progress and restart
            if c == '%':
                self.notifyProgress(int(progressstring))
                progressstring = ""
            # not reading a digit -> therefore restart
            elif c not in digits:
                progressstring = ""
            # add digit to progressstring
            else:
                progressstring += c

        # retrieve stderr
        err = p.stderr.read()

        if self.re_wrongpwd.search(err):
            raise PasswordError

        elif self.re_wrongcrc.search(err):
            raise CRCError(err)

        elif err.strip():  #: raise error if anything is on stderr
            raise ArchiveError(err)

        if p.returncode:
            raise ArchiveError(_("Process return code: %d") % p.returncode)

        if not self.files:
            self.files = self.list(password)


    def getDeleteFiles(self):
        files = []

        for i in (1, 2):
            try:
                dir, name = os.path.split(self.filename)

                part     = self.getattr(self, "re_rarpart%d" % i).search(name).group(1)
                new_name = name[::-1].replace((".part%s.rar" % part)[::-1], ".part*.rar"[::-1], 1)[::-1]
                file     = fs_encode(os.path.join(dir, new_name)

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

        self.manager.logDebug(" ".join(call))

        p = Popen(call, stdout=PIPE, stderr=PIPE)
        return p
