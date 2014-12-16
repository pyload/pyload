# -*- coding: utf-8 -*-

import sys
import zipfile

from module.plugins.internal.AbstractExtractor import AbtractExtractor, WrongPassword, ArchiveError


class UnZip(AbtractExtractor):
    __name__    = "UnZip"
    __version__ = "0.11"

    __description__ = """Zip extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    @staticmethod
    def checkDeps():
        return sys.version_info[:2] >= (2, 6)


    @staticmethod
    def getTargets(files_ids):
        result = []

        for file, id in files_ids:
            if file.endswith(".zip"):
                result.append((file, id))

        return result


    def extract(self, progress, password=None):
        try:
            z = zipfile.ZipFile(self.file)
            self.files = z.namelist()
            z.extractall(self.out, pwd=password)

        except (BadZipfile, LargeZipFile), e:
            raise ArchiveError(e)

        except RuntimeError, e:
            if e is "Bad password for file":
                raise WrongPassword
            else:
                raise ArchiveError(e)


    def getDeleteFiles(self):
        return [self.file]
