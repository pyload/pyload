# -*- coding: utf-8 -*-

import os
import re
import subprocess

from module.plugins.internal.UnRar import ArchiveError, CRCError, PasswordError, UnRar, renice
from module.utils import fs_encode, save_join as fs_join


class SevenZip(UnRar):
    __name__    = "SevenZip"
    __version__ = "0.14"
    __status__  = "testing"

    __description__ = """7-Zip extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Michael Nowak" , ""                 ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    CMD        = "7z"
    EXTENSIONS = [".7z", ".xz", ".zip", ".gz", ".gzip", ".tgz", ".bz2", ".bzip2",
                  ".tbz2", ".tbz", ".tar", ".wim", ".swm", ".lzma", ".rar", ".cab",
                  ".arj", ".z", ".taz", ".cpio", ".rpm", ".deb", ".lzh", ".lha",
                  ".chm", ".chw", ".hxs", ".iso", ".msi", ".doc", ".xls", ".ppt",
                  ".dmg", ".xar", ".hfs", ".exe", ".ntfs", ".fat", ".vhd", ".mbr",
                  ".squashfs", ".cramfs", ".scap"]


    #@NOTE: there are some more uncovered 7z formats
    re_filelist = re.compile(r'([\d\:]+)\s+([\d\:]+)\s+([\w\.]+)\s+(\d+)\s+(\d+)\s+(.+)')
    re_wrongpwd = re.compile(r'(Can not open encrypted archive|Wrong password|Encrypted\s+\=\s+\+)', re.I)
    re_wrongcrc = re.compile(r'CRC Failed|Can not open file', re.I)
    re_version  = re.compile(r'7-Zip\s(?:\[64\]\s)?(\d+\.\d+)', re.I)


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
            m = cls.re_version.search(out)
            if m is not None:
                cls.VERSION = m.group(1)

            return True


    def verify(self, password):
        #: 7z can't distinguish crc and pw error in test
        p = self.call_cmd("l", "-slt", fs_encode(self.filename))
        out, err = p.communicate()

        if self.re_wrongpwd.search(out):
            raise PasswordError

        if self.re_wrongpwd.search(err):
            raise PasswordError

        if self.re_wrongcrc.search(err):
            raise CRCError(err)



    def check(self, password):
        p = self.call_cmd("l", "-slt", fs_encode(self.filename))
        out, err = p.communicate()

        #: Check if output or error macthes the 'wrong password'-Regexp
        if self.re_wrongpwd.search(out):
            raise PasswordError

        if self.re_wrongcrc.search(out):
            raise CRCError(_("Header protected"))


    def repair(self):
        return False


    def extract(self, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_cmd(command, '-o' + self.out, fs_encode(self.filename), password=password)

        renice(p.pid, self.renice)

        #: Communicate and retrieve stderr
        self._progress(p)
        err = p.stderr.read().strip()

        if err:
            if self.re_wrongpwd.search(err):
                raise PasswordError

            elif self.re_wrongcrc.search(err):
                raise CRCError(err)

            else:  #: Raise error if anything is on stderr
                raise ArchiveError(err)

        if p.returncode > 1:
            raise ArchiveError(_("Process return code: %d") % p.returncode)

        self.files = self.list(password)


    def list(self, password=None):
        command = "l" if self.fullpath else "l"

        p = self.call_cmd(command, fs_encode(self.filename), password=password)
        out, err = p.communicate()

        if "Can not open" in err:
            raise ArchiveError(_("Cannot open file"))

        if p.returncode > 1:
            raise ArchiveError(_("Process return code: %d") % p.returncode)

        result = set()
        for groups in self.re_filelist.findall(out):
            f = groups[-1].strip()
            result.add(fs_join(self.out, f))

        return list(result)


    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        #: Overwrite flag
        if self.overwrite:
            args.append("-y")

        #: Set a password
        if "password" in kwargs and kwargs['password']:
            args.append("-p%s" % kwargs['password'])
        else:
            args.append("-p-")

        #@NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [self.CMD, command] + args + list(xargs)

        self.log_debug(" ".join(call))

        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p
