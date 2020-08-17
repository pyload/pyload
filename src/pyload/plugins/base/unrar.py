# -*- coding: utf-8 -*-

import os
import re
import subprocess

from pyload import PKGDIR
from pyload.core.utils.old import decode

from ..helpers import renice
from .extractor import ArchiveError, BaseExtractor, CRCError, PasswordError


class UnRar(BaseExtractor):
    __name__ = "UnRar"
    __type__ = "extractor"
    __version__ = "1.38"
    __status__ = "testing"

    __config__ = [("ignore_warnings", "bool", "Ignore unrar warnings", False)]

    __description__ = """RAR extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Immenz", "immenz@gmx.net"),
        ("GammaCode", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    CMD = "unrar"
    EXTENSIONS = [
        "rar",
        "cab",
        "arj",
        "lzh",
        "tar",
        "gz",
        "ace",
        "uue",
        "bz2",
        "jar",
        "iso",
        "xz",
        "z",
    ]

    _RE_PART = re.compile(r"\.(part|r)\d+(\.rar|\.rev)?(\.bad)?", re.I)
    _RE_FIXNAME = re.compile(r"Building (.+)")
    _RE_FILES = re.compile(
        r"^(.)(\s*[\w\-.]+)\s+(\d+\s+)+(?:\d+\%\s+)?[\d\-]{8,}\s+[\d\:]{5}", re.I | re.M
    )
    _RE_BADPWD = re.compile(r"password", re.I)
    _RE_BADCRC = re.compile(
        r"encrypted|damaged|CRC failed|checksum error|corrupt", re.I
    )
    _RE_VERSION = re.compile(r"(?:UN)?RAR\s(\d+\.\d+)", re.I)

    @classmethod
    def find(cls):
        try:
            if os.name == "nt":
                cls.CMD = os.path.join(PKGDIR, "lib", "RAR.exe")
            else:
                cls.CMD = "rar"

            p = subprocess.Popen(
                [cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = (r.strip() if r else "" for r in p.communicate())
            # cls.__name__ = "RAR"
            cls.REPAIR = True

        except OSError:
            try:
                if os.name == "nt":
                    cls.CMD = os.path.join(PKGDIR, "lib", "UnRAR.exe")
                else:
                    cls.CMD = "unrar"

                p = subprocess.Popen(
                    [cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                out, err = (r.strip() if r else "" for r in p.communicate())

            except OSError:
                return False

        m = cls._RE_VERSION.search(out)
        if m is not None:
            cls.VERSION = m.group(1)

        return True

    @classmethod
    def ismultipart(cls, filename):
        return cls._RE_PART.search(filename) is not None

    def verify(self, password=None):
        p = self.call_cmd("l", "-v", self.filename, password=password)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if self._RE_BADPWD.search(err):
            raise PasswordError

        if self._RE_BADCRC.search(err):
            raise CRCError(err)

        #: Output only used to check if passworded files are present
        for attr in self._RE_FILES.findall(out):
            if attr[0].startswith("*"):
                raise PasswordError

    def repair(self):
        p = self.call_cmd("rc", self.filename)

        #: Communicate and retrieve stderr
        self.progress(p)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if err or p.returncode:
            p = self.call_cmd("r", self.filename)

            # communicate and retrieve stderr
            self.progress(p)
            out, err = (r.strip() if r else "" for r in p.communicate())

            if err or p.returncode:
                return False

            else:
                dir = os.path.dirname(self.filename)
                name = self._RE_FIXNAME.search(out).group(1)

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

        p = self.call_cmd(command, self.filename, self.dest, password=password)

        #: Communicate and retrieve stderr
        self.progress(p)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if err:
            if self._RE_BADPWD.search(err):
                raise PasswordError

            elif self._RE_BADCRC.search(err):
                raise CRCError(err)

            elif self.config.get("ignore_warnings", False) and err.startswith(
                "WARNING:"
            ):
                pass

            else:  #: Raise error if anything is on stderr
                raise ArchiveError(err)

        if p.returncode:
            raise ArchiveError(self._("Process return code: {}").format(p.returncode))

        return self.list(password)

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
        command = "vb" if self.fullpath else "lb"

        p = self.call_cmd(command, "-v", self.filename, password=password)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if "Cannot open" in err:
            raise ArchiveError(self._("Cannot open file"))

        if err:  #: Only log error at this point
            self.log_error(err)

        result = set()
        if not self.fullpath and self.VERSION.startswith("5"):
            # NOTE: Unrar 5 always list full path
            for filename in decode(out).splitlines():
                filename = os.path.join(self.dest, os.path.basename(filename.strip()))
                if os.path.isfile(filename):
                    result.add(os.path.join(self.dest, os.path.basename(filename)))
        else:
            if self.fullpath:
                for filename in decode(out).splitlines():
                    # Unrar fails to list all directories for some archives
                    filename = filename.strip()
                    while filename:
                        fabs = os.path.join(self.dest, filename)
                        if fabs not in result:
                            result.add(fabs)
                            filename = os.path.dirname(filename)
                        else:
                            break
            else:
                for filename in decode(out).splitlines():
                    result.add(os.path.join(self.dest, filename.strip()))

        self.files = list(result)
        return self.files

    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        #: Overwrite flag
        if self.overwrite:
            args.append("-o+")
        else:
            args.append("-o-")
            args.append("-or")

        for word in self.excludefiles:
            args.append("-x{}".format(word.strip()))

        #: Assume yes on all queries
        args.append("-y")

        #: Set a password
        password = kwargs.get("password")

        if password:
            args.append("-p{}".format(password))
        else:
            args.append("-p-")

        if self.keepbroken:
            args.append("-kb")

        # NOTE: return codes are not reliable, some kind of threading, cleanup
        # whatever issue
        call = [self.CMD, command] + args + list(xargs)
        self.log_debug("EXECUTE " + " ".join(call))

        call = [str(cmd) for cmd in call]
        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        renice(p.pid, self.priority)

        return p
