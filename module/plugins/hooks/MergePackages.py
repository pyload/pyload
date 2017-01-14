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
    __version__ = "0.01"
    __description__ = "Merge new added package with existing one if has same name"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("exactmatch", "bool", "Exact match", "False"),
        ("samefolder", "bool", "Force merge if same saving folder", "False"),
        ("samelist", "bool", "Only merge if same list destination too", "True")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def linksAdded(self, links, pid):
        # self.logDebug("self.linksAdded")
        pypack = self.getPackageInfo(pid)
        queue = self.getQueue()
        collector = self.getCollector()
        exactmatch = self.getConf("exactmatch")
        samefolder = self.getConf("samefolder")
        samelist = self.getConf("samelist")
        packname = pypack.name if not exactmatch else sub('[^A-Za-z0-9]+', '', pypack.name).lower()
        packfolder = pypack.folder
        if samelist:
            lists = [queue] if pypack.queue else [collector]
        else:
            lists = [queue, collector]
        for list in lists:
            for p in list:
                pname = p.name if not exactmatch else sub('[^A-Za-z0-9]+', '', p.name).lower()
                if pname == packname or p.folder == packfolder if samefolder else True:
                    self.logInfo("Merging %s links into %s package founded in %s list" % (pypack.name, p.name, "queue" if p.queue else "collector"))
                    self.addFiles(p.id, links)
                    links = None
                    return
