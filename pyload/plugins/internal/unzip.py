# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import unicode_literals

import zipfile
import sys

from pyload.plugins.internal.AbstractExtractor import AbtractExtractor


class UnZip(AbtractExtractor):
    __name__ = "UnZip"
    __version__ = "0.1"

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
