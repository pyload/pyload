# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

from builtins import object
from threading import RLock
from time import sleep, time

from pyload.manager.PullEvents import UpdateEvent
from pyload.utils.utils import formatSize, lock

statusMap = {
    "finished": 0,
    "offline": 1,
    "online": 2,
    "queued": 3,
    "skipped": 4,
    "waiting": 5,
    "temp. offline": 6,
    "starting": 7,
    "failed": 8,
    "aborted": 9,
    "decrypting": 10,
    "custom": 11,
    "downloading": 12,
    "processing": 13,
    "unknown": 14,
}


def setSize(self, value):
    self._size = int(value)


class PyFile(object):
    """
    Represents a file object at runtime
    """
    __slots__ = (
        "m",
        "id",
        "url",
        "name",
        "size",
        "_size",
        "status",
        "pluginname",
        "packageid",
        "error",
        "order",
        "lock",
        "plugin",
        "waitUntil",
        "active",
        "abort",
        "statusname",
        "reconnected",
        "progress",
        "maxprogress",
        "pluginmodule",
        "pluginclass")

    def __init__(
            self,
            manager,
            id,
            url,
            name,
            size,
            status,
            error,
            pluginname,
            package,
            order):
        self.m = manager

        self.id = int(id)
        self.url = url
        self.name = name
        self.size = size
        self.status = status
        self.pluginname = pluginname
        self.packageid = package  # should not be used, use package() instead
        self.error = error
        self.order = order
        # database information ends here

        self.lock = RLock()

        self.plugin = None
        #self.download = None

        self.waitUntil = 0  # time() + time to wait

        # status attributes
        self.active = False  # obsolete?
        self.abort = False
        self.reconnected = False

        self.statusname = None

        self.progress = 0
        self.maxprogress = 100

        self.m.cache[int(id)] = self

    # will convert all sizes to ints
    size = property(lambda self: self._size, setSize)

    def __repr__(self):
        return "PyFile {}: {}@{}".format(self.id, self.name, self.pluginname)

    @lock
    def initPlugin(self):
        """ inits plugin instance """
        if not self.plugin:
            self.pluginmodule = self.m.pyload.pluginManager.getPlugin(self.pluginname)
            self.pluginclass = getattr(
                self.pluginmodule,
                self.m.pyload.pluginManager.getPluginName(
                    self.pluginname))
            self.plugin = self.pluginclass(self)

    @lock
    def hasPlugin(self):
        """Thread safe way to determine this file has initialized plugin attribute

        :return:
        """
        return hasattr(self, "plugin") and self.plugin

    def package(self):
        """ return package instance"""
        return self.m.getPackage(self.packageid)

    def setStatus(self, status):
        self.status = statusMap[status]
        self.sync()  # TODO: needed aslong no better job approving exists

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
        self.m.updateLink(self)

    @lock
    def release(self):
        """sync and remove from cache"""
        # file has valid package
        if self.packageid > 0:
            self.sync()

        if hasattr(self, "plugin") and self.plugin:
            self.plugin.clean()
            del self.plugin

        self.m.releaseLink(self.id)

    def delete(self):
        """delete pyfile from database"""
        self.m.deleteLink(self.id)

    def toDict(self):
        """return dict with all information for interface"""
        return self.toDbDict()

    def toDbDict(self):
        """return data as dict for databse

        format:

        {
            id: {'url': url, 'name': name ... }
        }

        """
        return {
            self.id: {
                'id': self.id,
                'url': self.url,
                'name': self.name,
                'plugin': self.pluginname,
                'size': self.getSize(),
                'format_size': self.formatSize(),
                'status': self.status,
                'statusmsg': self.getStatusName(),
                'package': self.packageid,
                'error': self.error,
                'order': self.order
            }
        }

    def abortDownload(self):
        """abort pyfile if possible"""
        while self.id in self.m.pyload.threadManager.processingIds():
            self.abort = True
            if self.plugin and self.plugin.req:
                self.plugin.req.abortDownloads()
            sleep(0.1)

        self.abort = False
        if self.hasPlugin() and self.plugin.req:
            self.plugin.req.abortDownloads()

        self.release()

    def finishIfDone(self):
        """set status to finish and release file if every thread is finished with it"""

        if self.id in self.m.pyload.threadManager.processingIds():
            return False

        self.setStatus("finished")
        self.release()
        self.m.checkAllLinksFinished()
        return True

    def checkIfProcessed(self):
        self.m.checkAllLinksProcessed(self.id)

    def formatWait(self):
        """ formats and return wait time in humanreadable format """
        seconds = self.waitUntil - time()

        if seconds < 0:
            return "00:00:00"

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "{:2d}:{:2d}:{:2d}".format(hours, minutes, seconds)

    def formatSize(self):
        """ formats size to readable format """
        return formatSize(self.getSize())

    def formatETA(self):
        """ formats eta to readable format """
        seconds = self.getETA()

        if seconds < 0:
            return "00:00:00"

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "{:2d}:{:2d}:{:2d}".format(hours, minutes, seconds)

    def getSpeed(self):
        """ calculates speed """
        try:
            return self.plugin.req.speed
        except Exception:
            return 0

    def getETA(self):
        """ gets established time of arrival"""
        try:
            return self.getBytesLeft() // self.getSpeed()
        except Exception:
            return 0

    def getBytesLeft(self):
        """ gets bytes left """
        try:
            return self.plugin.req.size - self.plugin.req.arrived
        except Exception:
            return 0

    def getPercent(self):
        """ get % of download """
        if self.status == 12:
            try:
                return self.plugin.req.percent
            except Exception:
                return 0
        else:
            return self.progress

    def getSize(self):
        """ get size of download """
        try:
            if self.plugin.req.size:
                return self.plugin.req.size
            else:
                return self.size
        except Exception:
            return self.size

    def notifyChange(self):
        e = UpdateEvent(
            "file",
            self.id,
            "collector" if not self.package().queue else "queue")
        self.m.pyload.pullManager.addEvent(e)

    def setProgress(self, value):
        if not value == self.progress:
            self.progress = value
            self.notifyChange()
