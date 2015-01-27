# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import sys
import zipfile

from module.plugins.internal.Extractor import Extractor, ArchiveError, CRCError, PasswordError


class UnZip(Extractor):
    __name__    = "UnZip"
    __version__ = "1.03"

    __description__ = """Zip extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    EXTENSIONS = [".zip", ".zip64"]


    @classmethod
    def checkDeps(cls):
        return sys.version_info[:2] >= (2, 6)


    @classmethod
    def getTargets(cls, files_ids):
        return [(filename, id) for filename, id in files_ids if cls.isArchive(filename)]


    def extract(self, password=None):
        try:
            with zipfile.ZipFile(self.target, 'r', allowZip64=True) as z:
                z.setpassword(self.password)
                if not z.testzip():
                    z.extractall(self.out)
                    self.files = z.namelist()
                else:
                    raise CRCError

        except (BadZipfile, LargeZipFile), e:
            raise ArchiveError(e)

        except RuntimeError, e:
            if "encrypted" in e:
                raise PasswordError
            else:
                raise ArchiveError(e)
