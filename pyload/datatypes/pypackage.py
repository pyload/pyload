# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals
from builtins import object
from time import time

from pyload.Api import PackageInfo, PackageStatus
from pyload.utils.fs import join


class PyPackage(object):
    """
    Represents a package object at runtime
    """

    @staticmethod
    def fromInfoData(m, info):
        return PyPackage(m, info.pid, info.name, info.folder, info.root, info.owner,
            info.site, info.comment, info.password, info.added, info.tags, info.status, info.shared, info.packageorder)

    def __init__(self, manager, pid, name, folder, root, owner, site, comment, password, added, tags, status,
                 shared, packageorder):
        self.m = manager

        self.pid = pid
        self.name = name
        self.folder = folder
        self.root = root
        self.ownerid = owner
        self.site = site
        self.comment = comment
        self.password = password
        self.added = added
        self.tags = tags
        self.status = status
        self.shared = shared
        self.packageorder = packageorder
        self.timestamp = time()

        #: Finish event already fired
        self.setFinished = False

    @property
    def id(self):
        self.m.pyload.log.debug("Deprecated package attr .id, use .pid instead")
        return self.pid

    def isStale(self):
        return self.timestamp + 30 * 60 > time()

    def toInfoData(self):
        return PackageInfo(self.pid, self.name, self.folder, self.root, self.ownerid, self.site,
            self.comment, self.password, self.added, self.tags, self.status, self.shared, self.packageorder
        )

    def updateFromInfoData(self, pack):
        """ Updated allowed values from info data """
        for attr in PackageInfo.__slots__:
            if attr in ("site", "comment", "password"):
                setattr(self, attr, getattr(pack, attr))

    def getFiles(self):
        """get contaied files data"""
        return self.m.pyload.db.getAllFiles(package=self.pid)

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
        self.m.removePackage(self.id)

    def deleteIfEmpty(self):
        """  True if deleted  """
        if not len(self.getFiles()):
            self.delete()
            return True
        return False

    def notifyChange(self):
        self.m.pyload.eventManager.dispatchEvent("packageUpdated", self.id)


class RootPackage(PyPackage):
    def __init__(self, m, owner):
        PyPackage.__init__(self, m, -1, "root", "", owner, -2, "", "", "", 0, [], PackageStatus.Ok, False, 0)

    def getPath(self, name=""):
        return join(self.m.pyload.config["general"]["download_folder"], name)

    # no database operations
    def sync(self):
        pass

    def delete(self):
        pass

    def release(self):
        pass
