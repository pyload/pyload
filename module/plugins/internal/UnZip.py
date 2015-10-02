# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import sys
import zipfile

from module.plugins.internal.Extractor import Extractor, ArchiveError, CRCError, PasswordError


class UnZip(Extractor):
    __name__    = "UnZip"
    __version__ = "1.16"
    __status__  = "testing"

    __description__ = """Zip extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    VERSION    = "%s.%s.%s" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
    EXTENSIONS = [".zip", ".zip64"]


    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 6)


    def list(self, password=None):
        with zipfile.ZipFile(self.target, 'r', allowZip64=True) as z:
            z.setpassword(password)
            return z.namelist()


    def verify(self, password=None):
        with zipfile.ZipFile(self.target, 'r', allowZip64=True) as z:
            badfile = z.testzip()

            if badfile:
                raise CRCError(badfile)
            else:
                raise PasswordError


    def extract(self, password=None):
        try:
            with zipfile.ZipFile(self.target, 'r', allowZip64=True) as z:
                z.setpassword(password)

                badfile = z.testzip()

                if badfile:
                    raise CRCError(badfile)
                else:
                    z.extractall(self.out)

        except (zipfile.BadZipfile, zipfile.LargeZipFile), e:
            raise ArchiveError(e)

        except RuntimeError, e:
            if "encrypted" in e:
                raise PasswordError
            else:
                raise ArchiveError(e)
        else:
            self.files = z.namelist()
