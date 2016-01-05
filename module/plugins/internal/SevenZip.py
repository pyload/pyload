# -*- coding: utf-8 -*-

import os
import re
import subprocess

from module.plugins.internal.UnRar import UnRar, ArchiveError, CRCError, PasswordError
from module.plugins.internal.misc import encode, fsjoin, renice


class SevenZip(UnRar):
    __name__    = "SevenZip"
    __type__    = "extractor"
    __version__ = "0.20"
    __status__  = "testing"

    __description__ = """7-Zip extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("Michael Nowak" , None               )]


    CMD        = "7z"
    EXTENSIONS = ["7z", "xz", "zip", "gz", "gzip", "tgz", "bz2", "bzip2", "tbz2",
                  "tbz", "tar", "wim", "swm", "lzma", "rar", "cab", "arj", "z",
                  "taz", "cpio", "rpm", "deb", "lzh", "lha", "chm", "chw", "hxs",
                  "iso", "msi", "doc", "xls", "ppt", "dmg", "xar", "hfs", "exe",
                  "ntfs", "fat", "vhd", "mbr", "squashfs", "cramfs", "scap"]

    #@NOTE: there are some more uncovered 7z formats
    _RE_FILES   = re.compile(r'([\d\:]+)\s+([\d\:]+)\s+([\w\.]+)\s+(\d+)\s+(\d+)\s+(.+)')
    _RE_BADPWD  = re.compile(r'(Can not open encrypted archive|Wrong password|Encrypted\s+\=\s+\+)', re.I)
    _RE_BADCRC  = re.compile(r'CRC Failed|Can not open file', re.I)
    _RE_VERSION = re.compile(r'7-Zip\s(?:\[64\]\s)?(\d+\.\d+)', re.I)


    @classmethod
    def find(cls):
        try:
            if os.name == "nt":
                cls.CMD = os.path.join(pypath, "7z.exe")

            p = subprocess.Popen([cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()

        except OSError:
            return False

        else:
            m = cls._RE_VERSION.search(out)
            if m is not None:
                cls.VERSION = m.group(1)

            return True


    def verify(self, password=None):
        #: 7z can't distinguish crc and pw error in test
        p = self.call_cmd("l", "-slt", self.target)
        out, err = p.communicate()

        if self._RE_BADPWD.search(out):
            raise PasswordError

        elif self._RE_BADPWD.search(err):
            raise PasswordError

        elif self._RE_BADCRC.search(out):
            raise CRCError(_("Header protected"))

        elif self._RE_BADCRC.search(err):
            raise CRCError(err)


    def extract(self, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_cmd(command, '-o' + self.dest, self.target, password=password)

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

        if p.returncode > 1:
            raise ArchiveError(_("Process return code: %d") % p.returncode)


    def list(self, password=None):
        command = "l" if self.fullpath else "l"

        p = self.call_cmd(command, self.target, password=password)
        out, err = p.communicate()

        if "Can not open" in err:
            raise ArchiveError(_("Cannot open file"))

        if p.returncode > 1:
            raise ArchiveError(_("Process return code: %d") % p.returncode)

        result = set()
        for groups in self._RE_FILES.findall(out):
            f = groups[-1].strip()
            result.add(fsjoin(self.dest, f))

        return list(result)


    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        #: Overwrite flag
        if self.overwrite:
            args.append("-y")

        #: Set a password
        password = kwargs.get('password')

        if password:
            args.append("-p%s" % password)
        else:
            args.append("-p-")

        #@NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [self.CMD, command] + args + list(xargs)
        self.log_debug("EXECUTE " + " ".join(call))

        call = map(encode, call)
        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        renice(p.pid, self.priority)

        return p
