# -*- coding: utf-8 -*-

from __future__ import with_statement

import sys
import zipfile

from module.plugins.internal.Extractor import Extractor, ArchiveError, CRCError, PasswordError


class UnZip(Extractor):
    __name__    = "UnZip"
    __version__ = "1.01"

    __description__ = """Zip extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    EXTENSIONS = ["zip", "zip64"]


    @classmethod
    def checkDeps(cls):
        return sys.version_info[:2] >= (2, 6)


    @classmethod
    def isArchive(cls, file):
        return zipfile.is_zipfile(file)


    def verify(self):
        try:
            with zipfile.ZipFile(self.file, 'r', allowZip64=True) as z:
                z.setpassword(self.password)
                badcrc = z.testzip()

        except (BadZipfile, LargeZipFile), e:
            raise ArchiveError(e)

        except RuntimeError, e:
            if 'encrypted' in e:
                raise PasswordError
            else:
                raise ArchiveError(e)

        else:
            if badcrc:
                raise CRCError

        if not self.list():
            raise ArchiveError("Empty archive")


    def list(self):
        try:
            with zipfile.ZipFile(self.file, 'r', allowZip64=True) as z:
                z.setpassword(self.password)
                return z.namelist()
        except Exception:
            return list()


    def extract(self, progress=lambda x: None):
        try:
            with zipfile.ZipFile(self.file, 'r', allowZip64=True) as z:
                progress(0)
                z.extractall(self.out, pwd=self.password)
                progress(100)

        except (BadZipfile, LargeZipFile), e:
            raise ArchiveError(e)

        except RuntimeError, e:
            if e is "Bad password for file":
                raise PasswordError
            else:
                raise ArchiveError(e)

        finally:
            self.files = self.list()


    def getDeleteFiles(self):
        return [self.file]
