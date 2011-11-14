# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
"""

import zipfile
import sys

from module.plugins.internal.AbstractExtractor import AbtractExtractor

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