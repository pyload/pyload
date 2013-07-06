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

from module.plugins.Hook import Hook
from re import sub


class MergePackages(Hook):
    __name__ = "MergePackages"
    __version__ = "0.03"
    __description__ = "Merges added package with an existing one if same name"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("exactmatch", "bool", "Exact match", "False")
        #("samefolder", "bool", "Ignore name if same saving folder", "False")
        #("samelist", "bool", "Merge if same list destination too", "True")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    event_map = {"linksAdded": "linksAdded"}

    def linksAdded(self, links, pid):
        pypack = self.api.getPackageInfo(pid)
        queue = self.api.getQueue()
        collector = self.api.getCollector()
        exactmatch = self.getConfig("exactmatch")
        samesamefolder = False
        samelist = False
        #samefolder = self.getConfig("samefolder")
        #samelist = self.getConfig("samelist")
        pname = pypack.name if not exactmatch else sub('[^A-Za-z0-9]+', '', pypack.name).lower()
        self.logDebug(pname)
        #packfolder = pypack.folder
        #self.logDebug(packfolder)
        if samelist:
            lists = [queue] if pypack.queue else [collector]
        else:
            lists = [queue, collector]
        for l in lists:
            for listpack in l:
                lpname = listpack.name if not exactmatch else sub('[^A-Za-z0-9]+', '', listpack.name).lower()
                if lpname == pname or (listpack.folder == packfolder if samefolder else False):
                    msg = "merging %s links into %s package"
                    #msg = "merging %s links into %s package found in %s list"
                    self.logInfo(msg % (pypack.name, listpack.name))
                    #self.logInfo(msg % (pypack.name, listpack.name, "queue" if listpack.queue else "collector"))
                    self.api.addFiles(listpack.id, links)
                    del links[:]

    def setup(self):
        self.api = self.core.api
