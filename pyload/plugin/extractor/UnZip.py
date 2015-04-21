# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import sys
import zipfile

from pyload.plugin.Extractor import Extractor, ArchiveError, CRCError, PasswordError
from pyload.utils import fs_encode


class UnZip(Extractor):
    __name    = "UnZip"
    __type    = "extractor"
    __version = "1.12"

    __description = """Zip extractor plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    EXTENSIONS = [".zip", ".zip64"]
    NAME       = __name__
    VERSION    = "(python %s.%s.%s)" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])


    @classmethod
    def isUsable(cls):
        return sys.version_info[:2] >= (2, 6)


    def list(self, password=None):
        with zipfile.ZipFile(fs_encode(self.filename), 'r', allowZip64=True) as z:
            z.setpassword(password)
            return z.namelist()


    def check(self, password):
        pass


    def verify(self):
        with zipfile.ZipFile(fs_encode(self.filename), 'r', allowZip64=True) as z:
            badfile = z.testzip()

            if badfile:
                raise CRCError(badfile)
            else:
                raise PasswordError


    def extract(self, password=None):
        try:
            with zipfile.ZipFile(fs_encode(self.filename), 'r', allowZip64=True) as z:
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
