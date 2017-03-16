# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, division, unicode_literals

import os
from builtins import object
from time import time

from enum import IntFlag
from future import standard_library

from .init import BaseObject, ExceptionObject

standard_library.install_aliases()


class PackageStatus(IntFlag):
    Ok = 0
    Paused = 1
    Folder = 2
    Remote = 3


class PackageDoesNotExist(ExceptionObject):
    __slots__ = ['pid']

    def __init__(self, pid=None):
        self.pid = pid


class PackageInfo(BaseObject):
    __slots__ = ['pid', 'name', 'folder', 'root', 'owner', 'site', 'comment', 'password',
                 'added', 'tags', 'status', 'shared', 'packageorder', 'stats', 'fids', 'pids']

    def __init__(self, pid=None, name=None, folder=None, root=None, owner=None, site=None, comment=None, password=None,
                 added=None, tags=None, status=None, shared=None, packageorder=None, stats=None, fids=None, pids=None):
        self.pid = pid
        self.name = name
        self.folder = folder
        self.root = root
        self.owner = owner
        self.site = site
        self.comment = comment
        self.password = password
        self.added = added
        self.tags = tags
        self.status = status
        self.shared = shared
        self.packageorder = packageorder
        self.stats = stats
        self.fids = fids
        self.pids = pids


class PackageStats(BaseObject):
    __slots__ = ['linkstotal', 'linksdone', 'sizetotal', 'sizedone']

    def __init__(self, linkstotal=None, linksdone=None,
                 sizetotal=None, sizedone=None):
        self.linkstotal = linkstotal
        self.linksdone = linksdone
        self.sizetotal = sizetotal
        self.sizedone = sizedone


class PyPackage(BaseObject):
    """
    Represents a package object at runtime.
    """
    __slots__ = ['added', 'comment', 'comment', 'folder', 'manager', 'name',
                 'ownerid', 'packageorder', 'password', 'password', 'pid',
                 'root', 'set_finished', 'shared', 'site', 'site', 'status',
                 'tags', 'timestamp']

    @staticmethod
    def from_info_data(m, info):
        return PyPackage(m, info.pid, info.name, info.folder, info.root, info.owner,
                         info.site, info.comment, info.password, info.added, info.tags, info.status, info.shared, info.packageorder)

    def __init__(self, manager, pid, name, folder, root, owner, site, comment, password, added, tags, status,
                 shared, packageorder):
        self.manager = manager

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
        self.set_finished = False

    def is_stale(self):
        return self.timestamp + 30 * 60 > time()

    def to_info_data(self):
        return PackageInfo(
            self.pid, self.name, self.folder, self.root, self.ownerid, self.site,
            self.comment, self.password, self.added, self.tags, self.status,
            self.shared, self.packageorder)

    def update_from_info_data(self, pack):
        """
        Updated allowed values from info data.
        """
        for attr in PackageInfo.__slots__:
            if attr in ("site", "comment", "password"):
                setattr(self, attr, getattr(pack, attr))

    def get_files(self):
        """
        Get contaied files data.
        """
        return self.manager.pyload.db.get_all_files(package=self.pid)

    def get_path(self, name=""):
        self.timestamp = time()
        return os.path.join(self.manager.get_package(
            self.root).get_path(), self.folder, name)

    def sync(self):
        """
        Sync with db.
        """
        self.manager.update_package(self)

    def release(self):
        """
        Sync and delete from cache.
        """
        self.sync()
        self.manager.release_package(self.id)

    def delete(self):
        self.manager.remove_package(self.id)

    def delete_if_empty(self):
        """
        True if deleted.
        """
        if not len(self.get_files()):
            self.delete()
            return True
        return False

    def notify_change(self):
        self.manager.pyload.evm.fire("packageUpdated", self.id)


class RootPackage(PyPackage):

    __slots__ = []

    def __init__(self, m, owner):
        PyPackage.__init__(self, m, -1, "root", "", owner, -2,
                           "", "", "", 0, [], PackageStatus.Ok, False, 0)

    def get_path(self, name=""):
        return os.path.join(self.manager.pyload.config.get(
            'general', 'storage_folder'), name)

    # no database operations
    def sync(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError
