#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2012 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from time import time

from module.Api import PackageInfo, PackageStatus
from module.utils.fs import join

class PyPackage:
    """
    Represents a package object at runtime
    """

    @staticmethod
    def fromInfoData(m, info):
        return PyPackage(m, info.pid, info.name, info.folder, info.root, info.owner,
            info.site, info.comment, info.password, info.added, info.tags, info.status, info.packageorder)

    def __init__(self, manager, pid, name, folder, root, owner, site, comment, password, added, tags, status, packageorder):
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
        self.packageorder = packageorder
        self.timestamp = time()

        #: Finish event already fired
        self.setFinished = False

    @property
    def id(self):
        self.m.core.log.debug("Deprecated package attr .id, use .pid instead")
        return self.pid

    def isStale(self):
        return self.timestamp + 30 * 60 > time()

    def toInfoData(self):
        return PackageInfo(self.pid, self.name, self.folder, self.root, self.ownerid, self.site,
            self.comment, self.password, self.added, self.tags, self.status, self.packageorder
        )

    def getChildren(self):
        """get information about contained links"""
        return self.m.getPackageData(self.pid)["links"]

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
    def __init__(self, m, owner):
        PyPackage.__init__(self, m, -1, "root", "", owner, -2, "", "", "", 0, [], PackageStatus.Ok, 0)

    def getPath(self, name=""):
        return join(self.m.core.config["general"]["download_folder"], name)

    # no database operations
    def sync(self):
        pass

    def delete(self):
        pass

    def release(self):
        pass