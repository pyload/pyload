# -*- coding: utf-8 -*-

import os
import sys
import zipfile

from .extractor import ArchiveError, BaseExtractor, CRCError, PasswordError


class UnZip(BaseExtractor):
    __name__ = "UnZip"
    __type__ = "extractor"
    __version__ = "1.25"
    __status__ = "stable"

    __description__ = """ZIP extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    VERSION = "{}.{}.{}".format(
        sys.version_info[0], sys.version_info[1], sys.version_info[2]
    )

    @classmethod
    def archivetype(cls, filename):
        return "zip" if cls.isarchive(filename) else None

    @classmethod
    def isarchive(cls, filename):
        return zipfile.is_zipfile(os.fsdecode(filename))

    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 6)

    def list(self, password=None):
        with zipfile.ZipFile(self.filename, "r") as z:
            z.setpassword(password)
            self.files = z.namelist()
        return self.files

    def verify(self, password=None):
        try:
            with zipfile.ZipFile(self.filename, "r") as z:
                z.setpassword(password)
                badfile = z.testzip()
                if badfile is not None:
                    raise CRCError(badfile)

        except (zipfile.BadZipfile, zipfile.LargeZipFile) as exc:
            raise ArchiveError(exc)

        except RuntimeError as exc:
            if "encrypted" in exc.args[0] or "Bad password" in exc.args[0]:
                raise PasswordError(exc)
            else:
                raise CRCError(exc)

    def extract(self, password=None):
        self.verify(password)

        try:
            with zipfile.ZipFile(self.filename, "r") as z:
                z.setpassword(password)
                z.extractall(self.dest)
                self.files = z.namelist()
            return self.files

        except RuntimeError as exc:
            raise ArchiveError(exc)
