# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import sys
import zipfile

from .Extractor import ArchiveError, CRCError, Extractor, PasswordError
from .misc import fs_encode, fsjoin


class UnZip(Extractor):
    __name__ = "UnZip"
    __type__ = "extractor"
    __version__ = "1.27"
    __status__ = "stable"

    __description__ = """ZIP extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    VERSION = "%s.%s.%s" % (sys.version_info[0],
                            sys.version_info[1],
                            sys.version_info[2])

    @classmethod
    def archivetype(cls, filename):
        try:
            return "zip" if cls.isarchive(filename) else None

        except IOError:
            return None

    @classmethod
    def isarchive(cls, filename):
        #: zipfile only checks for 'End of archive' so we have to check ourselves for 'start of archive'
        try:
            with open(fs_encode(filename), "rb") as f:
                data = f.read(4)
                if data != "PK\003\004":
                    return False

                else:
                    return zipfile.is_zipfile(f)

        except IOError:
            return False

    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 6)

    def list(self, password=None):
        with zipfile.ZipFile(self.filename, 'r') as z:
            z.setpassword(password)
            self.files = [fs_encode(self.dest, _f) for _f in z.namelist() if not _f[-1] != os.path.sep]
        return self.files

    def verify(self, password=None):
        try:
            with zipfile.ZipFile(self.filename, 'r') as z:
                z.setpassword(password)
                badfile = z.testzip()
                if badfile is not None:
                    raise CRCError(badfile)

        except (zipfile.BadZipfile, zipfile.LargeZipFile), e:
            raise ArchiveError(e)

        except RuntimeError, e:
            if "encrypted" in e.args[0] or "Bad password" in e.args[0]:
                raise PasswordError(e)
            else:
                raise CRCError(e)

    def extract(self, password=None):
        self.verify(password)

        try:
            with zipfile.ZipFile(self.filename, 'r') as z:
                z.setpassword(password)
                z.extractall(self.dest)
                self.files = z.namelist()
            return self.files

        except RuntimeError, e:
            raise ArchiveError(e)
