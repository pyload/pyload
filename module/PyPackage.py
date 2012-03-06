#!/usr/bin/env python
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

from time import time

from module.utils.fs import join

from Api import PackageInfo, PackageStatus

class PyPackage:
    """
    Represents a package object at runtime
    """

    @staticmethod
    def fromInfoData(m, info):
        return PyPackage(m, info.pid, info.name, info.folder, info.root,
            info.site, info.comment, info.password, info.added, info.status, info.packageorder)

    def __init__(self, manager, pid, name, folder, root, site, comment, password, added, status, packageorder):
        self.m = manager

        self.pid = pid
        self.name = name
        self.folder = folder
        self.root = root
        self.site = site
        self.comment = comment
        self.password = password
        self.added = added
        self.status = status
        self.packageorder = packageorder
        self.timestamp = time()

    @property
    def id(self):
        self.m.core.log.debug("Deprecated package attr .id, use .pid instead")
        return self.pid

    def isStale(self):
        return self.timestamp + 30 * 60 > time()

    def toInfoData(self):
        return PackageInfo(self.pid, self.name, self.folder, self.root, self.site,
            self.comment, self.password, self.added, self.status, self.packageorder
        )

    def getChildren(self):
        """get information about contained links"""
        return self.m.getPackageData(self.id)["links"]

    def getPath(self, name=""):
        self.timestamp = time()
        return join(self.m.getPackage(self.root).getPath(), self.folder, name)

    def sync(self):
        """sync with db"""
        self.m.updatePackage(self)

    def release(self):
        """sync and delete from cache"""
        self.sync()
        self.m.releasePackage(self.id)

    def delete(self):
        self.m.deletePackage(self.id)

    def deleteIfEmpty(self):
        """  True if deleted  """
        if not len(self.getChildren()):
            self.delete()
            return True
        return False

    def notifyChange(self):
        self.m.core.eventManager.dispatchEvent("packageUpdated", self.id)


class RootPackage(PyPackage):
    def __init__(self, m):
        PyPackage.__init__(self, m, -1, "root", "", -2, "", "", "", 0, PackageStatus.Ok, 0)

    def getPath(self, name=""):
        return join(self.m.core.config["general"]["download_folder"], name)

    # no database operations
    def sync(self):
        pass

    def delete(self):
        pass

    def release(self):
        pass