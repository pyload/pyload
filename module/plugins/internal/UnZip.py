# -*- coding: utf-8 -*-

import sys
import zipfile

from module.plugins.internal.AbstractExtractor import AbtractExtractor


class UnZip(AbtractExtractor):
    __name__ = "UnZip"
    __version__ = "0.1"

    __description__ = """Zip extractor plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"


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
        z = zipfile.ZipFile(self.file)
        self.files = z.namelist()
        z.extractall(self.out)

    def getDeleteFiles(self):
        return [self.file]
