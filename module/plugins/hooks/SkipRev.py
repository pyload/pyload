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

    @author: Walter Purcaro
"""

from os.path import basename
from re import search

from module.plugins.Hook import Hook


class SkipRev(Hook):
    __name__ = "SkipRev"
    __version__ = "0.07"
    __description__ = "Skip download when filename has rev extension"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("number", "int", "Do not skip until rev part", "1")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def downloadPreparing(self, pyfile):
        # self.logDebug("self.downloadPreparing")
        name = basename(pyfile.name)
        if not name.endswith(".rev"):
            return
        number = self.getConfig("number")
        part = search(r'\.part(\d+)\.rev$', name)
        if not part or int(part.group(1)) <= number:
            return
        self.logInfo("Skipping " + name)
        pyfile.setStatus("skipped")
