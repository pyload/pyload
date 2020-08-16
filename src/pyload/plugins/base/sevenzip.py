# -*- coding: utf-8 -*-

import os
import re
import subprocess

from pyload import PKGDIR

from ..helpers import renice
from .extractor import ArchiveError, BaseExtractor, CRCError, PasswordError


class SevenZip(BaseExtractor):
    __name__ = "SevenZip"
    __type__ = "extractor"
    __version__ = "0.27"
    __status__ = "testing"

    __description__ = """7-Zip extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"), ("Michael Nowak", None)]

    CMD = "7z"
    EXTENSIONS = [
        ("7z", r"7z(?:\.\d{3})?"),
        "xz",
        "gz",
        "gzip",
        "tgz",
        "bz2",
        "bzip2",
        "tbz2",
        "tbz",
        "tar",
        "wim",
        "swm",
        "lzma",
        "rar",
        "cab",
        "arj",
        "z",
        "taz",
        "cpio",
        "rpm",
        "deb",
        "lzh",
        "lha",
        "chm",
        "chw",
        "hxs",
        "iso",
        "msi",
        "doc",
        "xls",
        "ppt",
        "dmg",
        "xar",
        "hfs",
        "exe",
        "ntfs",
        "fat",
        "vhd",
        "mbr",
        "squashfs",
        "cramfs",
        "scap",
    ]

    _RE_PART = re.compile(r"\.7z\.\d{3}|\.(part|r)\d+(\.rar|\.rev)?(\.bad)?", re.I)
    _RE_FILES = re.compile(
        r"([\d\-]+)\s+([\d\:]+)\s+([RHSA\.]+)\s+(\d+)\s+(\d+)\s+(.+)"
    )
    _RE_BADPWD = re.compile(
        r"(Can not open encrypted archive|Wrong password|Encrypted\s+\=\s+\+)", re.I
    )
    _RE_BADCRC = re.compile(r"CRC Failed|Can not open file", re.I)
    _RE_VERSION = re.compile(
        r"7-Zip\s(?:\(\w+\)\s)?(?:\[(?:32|64)\]\s)?(\d+\.\d+)", re.I
    )

    @classmethod
    def find(cls):
        try:
            if os.name == "nt":
                cls.CMD = os.path.join(PKGDIR, "lib", "7z.exe")

            p = subprocess.Popen(
                [cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = (r.strip() if r else "" for r in p.communicate())

        except OSError:
            return False

        else:
            m = cls._RE_VERSION.search(out)
            if m is not None:
                cls.VERSION = m.group(1)

            return True

    @classmethod
    def ismultipart(cls, filename):
        return cls._RE_PART.search(filename) is not None

    def verify(self, password=None):
        #: 7z can't distinguish crc and pw error in test
        p = self.call_cmd("l", "-slt", self.filename)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if self._RE_BADPWD.search(out):
            raise PasswordError

        elif self._RE_BADPWD.search(err):
            raise PasswordError

        elif self._RE_BADCRC.search(out):
            raise CRCError(self._("Header protected"))

        elif self._RE_BADCRC.search(err):
            raise CRCError(err)

    def progress(self, process):
        s = ""
        while True:
            c = process.stdout.read(1)
            #: Quit loop on eof
            if not c:
                break
            #: Reading a percentage sign -> set progress and restart
            if c == "%":
                self.pyfile.set_progress(int(s))
                s = ""
            #: Not reading a digit -> therefore restart
            elif not c.isdigit():
                s = ""
            #: Add digit to progressstring
            else:
                s += c

    def extract(self, password=None):
        command = "x" if self.fullpath else "e"

        p = self.call_cmd(command, "-o" + self.dest, self.filename, password=password)

        #: Communicate and retrieve stderr
        self.progress(p)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if err:
            if self._RE_BADPWD.search(err):
                raise PasswordError

            elif self._RE_BADCRC.search(err):
                raise CRCError(err)

            else:  #: Raise error if anything is on stderr
                raise ArchiveError(err)

        if p.returncode > 1:
            raise ArchiveError(self._("Process return code: {}").format(p.returncode))

    def chunks(self):
        files = []
        dir, name = os.path.split(self.filename)

        #: eventually Multipart Files
        files.extend(
            os.path.join(dir, os.path.basename(entry))
            for entry in os.listdir(dir)
            if self.ismultipart(entry)
            and self._RE_PART.sub("", name) == self._RE_PART.sub("", entry)
        )

        #: Actually extracted file
        if self.filename not in files:
            files.append(self.filename)

        return files

    def list(self, password=None):
        command = "l" if self.fullpath else "l"

        p = self.call_cmd(command, self.filename, password=password)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if any(e in err for e in ("Can not open", "cannot find the file")):
            raise ArchiveError(self._("Cannot open file"))

        if p.returncode > 1:
            raise ArchiveError(self._("Process return code: {}").format(p.returncode))

        files = set()
        for groups in self._RE_FILES.findall(out):
            f = groups[-1].strip()
            files.add(os.path.join(self.dest, f))

        self.files = list(files)

        return self.files

    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        #: Progress output
        if self.VERSION and float(self.VERSION) >= 15.08:
            args.append("-bsp1")

        #: Overwrite flag
        if self.overwrite:
            if self.VERSION and float(self.VERSION) >= 15.08:
                args.append("-aoa")

            else:
                args.append("-y")

        else:
            if self.VERSION and float(self.VERSION) >= 15.08:
                args.append("-aos")

        #: Exclude files
        for word in self.excludefiles:
            args.append("-xr!{}".format(word.strip()))

        #: Set a password
        password = kwargs.get("password")

        if password:
            args.append("-p{}".format(password))
        else:
            args.append("-p-")

        # NOTE: return codes are not reliable, some kind of threading, cleanup whatever issue
        call = [self.CMD, command] + args + list(xargs)
        self.log_debug("EXECUTE " + " ".join(call))

        call = [str(cmd) for cmd in call]
        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        renice(p.pid, self.priority)

        return p
