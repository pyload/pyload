# -*- coding: utf-8 -*-

import os
import sys
import zipfile
import fnmatch

from pyload.plugins.base.extractor import ArchiveError, BaseExtractor, CRCError, PasswordError


class UnZip(BaseExtractor):
    __name__ = "UnZip"
    __type__ = "extractor"
    __version__ = "1.28"
    __status__ = "stable"

    __description__ = """ZIP extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    VERSION = "{}.{}.{}".format(
        sys.version_info[0], sys.version_info[1], sys.version_info[2]
    )

    @classmethod
    def archivetype(cls, filename):
        try:
            return "zip" if cls.isarchive(filename) else None

        except IOError:
            return None

    @classmethod
    def isarchive(cls, filename):
        if os.path.splitext(filename)[1] != ".zip":
            return False

        #: zipfile only checks for 'End of archive' so we have to check ourselves for 'start of archive'
        try:
            with open(filename, "rb") as f:
                data = f.read(4)
                if data != b"PK\003\004":
                    return False

                else:
                    return zipfile.is_zipfile(f)

        except IOError:
            return False

    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 6)

    def list(self, password=None):
        with zipfile.ZipFile(self.filename, "r") as z:
            z.setpassword(password)
            self.files = [os.path.join(self.dest, _f)
                          for _f in z.namelist()
                          if _f[-1] != os.path.sep]

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
                members = (member for member in z.namelist()  
                           if not any(fnmatch.fnmatch(member, exclusion)
                           for exclusion in self.excludefiles))
                z.extractall(self.dest, members = members)
                self.files = [os.path.join(self.dest, _f)
                              for _f in z.namelist()
                              if _f[-1] != os.path.sep and _f in members]

            return self.files

        except RuntimeError as exc:
            raise ArchiveError(exc)
