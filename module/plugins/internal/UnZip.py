# -*- coding: utf-8 -*-

from __future__ import with_statement

import sys
import zipfile

from module.plugins.internal.Extractor import Extractor, ArchiveError, CRCError, PasswordError
from module.plugins.internal.misc import encode


class UnZip(Extractor):
    __name__    = "UnZip"
    __type__    = "extractor"
    __version__ = "1.21"
    __status__  = "stable"

    __description__ = """ZIP extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    VERSION = "%s.%s.%s" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])


    @classmethod
    def isarchive(cls, filename):
        return zipfile.is_zipfile(encode(filename))


    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 6)


    def list(self, password=None):
        with zipfile.ZipFile(self.target, 'r') as z:
            z.setpassword(password)
            return z.namelist()


    def verify(self, password=None):
        try:
            with zipfile.ZipFile(self.target, 'r') as z:
                z.setpassword(password)
                if z.testzip():
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
            with zipfile.ZipFile(self.target, 'r') as z:
                z.setpassword(password)
                z.extractall(self.dest)

        except RuntimeError, e:
            raise ArchiveError(e)
