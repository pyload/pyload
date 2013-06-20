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
    
    @author: mmichaa (Michael Nowak)
"""

import re
from glob import glob

from module.plugins.internal.AbstractSevenZip import AbstractSevenZip, renice

class SevenZipUnRar(AbstractSevenZip):
    __name__ = "SevenZipUnRar"
    __version__ = "0.1"

    # there are some more uncovered rar formats
    re_singlefile = re.compile(r"(.*\.r)ar$", re.I)
    re_splitfile = re.compile(r"(.*\.part)\d+\.rar$", re.I)
    re_partfile = re.compile(r"(.*\.r)[0-9]+$", re.I)

    def getDeleteFiles(self):
        if ".part" in self.file:
            return glob(re.sub("(?<=\.part)([01]+)", "*", self.file, re.IGNORECASE))
        # get files which matches .r* and filter unsuited files out
        parts = glob(re.sub(r"(?<=\.r)ar$", "*", self.file, re.IGNORECASE))
        return filter(lambda x: self.re_partfiles.match(x), parts)
