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

from time import sleep, time
from ReadWriteLock import ReadWriteLock

from pyload.Api import ProgressInfo, DownloadProgress, FileInfo, DownloadInfo, DownloadStatus
from pyload.utils import lock, read_lock
from pyload.utils.filetypes import guess_type

statusMap = {
    "none": 0,
    "offline": 1,
    "online": 2,
    "queued": 3,
    "paused": 4,
    "finished": 5,
    "skipped": 6,
    "failed": 7,
    "starting": 8,
    "waiting": 9,
    "downloading": 10,
    "temp. offline": 11,
    "aborted": 12,
    "decrypting": 13,
    "processing": 14,
    "custom": 15,
    "unknown": 16,
}


class PyFile(object):
    """
    Represents a file object at runtime
    """
    __slots__ = ("m", "fid", "_name", "_size", "filestatus", "media", "added", "fileorder",
                 "url", "pluginname", "hash", "status", "error", "packageid", "owner",
                 "lock", "plugin", "waitUntil", "abort", "statusname",
                 "reconnected", "pluginclass")

    @staticmethod
    def fromInfoData(m, info):
        f = PyFile(m, info.fid, info.name, info.size, info.status, info.media, info.added, info.fileorder,
                   "", "", "", DownloadStatus.NA, "", info.package, info.owner)
        if info.download:
            f.url = info.download.url
            f.pluginname = info.download.plugin
            f.hash = info.download.hash
            f.status = info.download.status
            f.error = info.download.error

        return f

    def __init__(self, manager, fid, name, size, filestatus, media, added, fileorder,
                 url, pluginname, hash, status, error, package, owner):

        self.m = manager

        self.fid = int(fid)
        self._name = name
        self._size = size
        self.filestatus = filestatus
        self.media = media
        self.added = added
        self.fileorder = fileorder
        self.url = url
        self.pluginname = pluginname
        self.hash = hash
        self.status = status
        self.error = error
        self.owner = owner
        self.packageid = package
        # database information ends here

        self.lock = ReadWriteLock()

        self.plugin = None

        self.waitUntil = 0 # time() + time to wait

        # status attributes
        self.abort = False
        self.reconnected = False
        self.statusname = None


    @property
    def id(self):
        self.m.core.log.debug("Deprecated attr .id, use .fid instead")
        return self.fid

    def setSize(self, value):
        self._size = int(value)

    # will convert all sizes to ints
    size = property(lambda self: self._size, setSize)

    def getName(self):
        try:
            if self.plugin.req.name:
                return self.plugin.req.name
            else:
                return self._name
        except:
            return self._name

    def setName(self, name):
        """ Only set unicode or utf8 strings as name """
        if type(name) == str:
            name = name.decode("utf8")

        # media type is updated if needed
        if self._name != name:
            self.media = guess_type(name)
            self._name = name

    name = property(getName, setName)

    def __repr__(self):
        return "<PyFile %s: %s@%s>" % (self.id, self.name, self.pluginname)

    @lock
    def initPlugin(self):
        """ inits plugin instance """
        if not self.plugin:
            self.pluginclass = self.m.core.pluginManager.getPlugin(self.pluginname)
            self.plugin = self.pluginclass(self)

    @read_lock
    def hasPlugin(self):
        """Thread safe way to determine this file has initialized plugin attribute"""
        return hasattr(self, "plugin") and self.plugin

    def package(self):
        """ return package instance"""
        return self.m.getPackage(self.packageid)

    def setStatus(self, status):
        self.status = statusMap[status]
        # needs to sync so status is written to database
        self.sync()

    def setCustomStatus(self, msg, status="processing"):
        self.statusname = msg
        self.setStatus(status)

    def getStatusName(self):
        if self.status not in (13, 14) or not self.statusname:
            return self.m.statusMsg[self.status]
        else:
            return self.statusname

    def hasStatus(self, status):
        return statusMap[status] == self.status

    def sync(self):
        """sync PyFile instance with database"""
        self.m.updateFile(self)

    @lock
    def release(self):
        """sync and remove from cache"""
        if hasattr(self, "plugin") and self.plugin:
            self.plugin.clean()
            del self.plugin

        self.m.releaseFile(self.fid)


    def toInfoData(self):
        return FileInfo(self.fid, self.getName(), self.packageid, self.owner, self.getSize(), self.filestatus,
                        self.media, self.added, self.fileorder, DownloadInfo(
                self.url, self.pluginname, self.hash, self.status, self.getStatusName(), self.error
            )
        )

    def getPath(self):
        pass

    def move(self, pid):
        pass

    @read_lock
    def abortDownload(self):
        """abort pyfile if possible"""
        # TODO: abort timeout, currently dead locks
        while self.id in self.m.core.threadManager.processingIds():
            self.abort = True
            if self.plugin and self.plugin.req:
                self.plugin.req.abort()
                if self.plugin.dl:
                    self.plugin.dl.abort()

            sleep(0.1)

        self.abort = False
        if self.plugin:
            self.plugin.req.abort()
            if self.plugin.dl:
                self.plugin.dl.abort()

        self.release()

    def finishIfDone(self):
        """set status to finish and release file if every thread is finished with it"""

        if self.id in self.m.core.threadManager.processingIds():
            return False

        self.setStatus("finished")
        self.release()
        self.m.checkAllLinksFinished()
        return True

    def checkIfProcessed(self):
        self.m.checkAllLinksProcessed(self.id)

    def getSpeed(self):
        """ calculates speed """
        try:
            return self.plugin.dl.speed
        except:
            return 0

    def getETA(self):
        """ gets established time of arrival / or waiting time"""
        try:
            if self.status == DownloadStatus.Waiting:
                return self.waitUntil - time()

            return self.getBytesLeft() / self.getSpeed()
        except:
            return 0

    def getBytesArrived(self):
        """ gets bytes arrived """
        try:
            return self.plugin.dl.arrived
        except:
            return 0

    def getBytesLeft(self):
        """ gets bytes left """
        try:
            return self.plugin.dl.size - self.plugin.dl.arrived
        except:
            return 0

    def getSize(self):
        """ get size of download """
        try:
            if self.plugin.dl.size:
                return self.plugin.dl.size
            else:
                return self.size
        except:
            return self.size

    def getProgressInfo(self):
        return ProgressInfo(self.pluginname, self.name, self.getStatusName(), self.getETA(),
                            self.getBytesArrived(), self.getSize(),
                            DownloadProgress(self.fid, self.packageid, self.getSpeed(), self.status))
