# -*- coding: utf-8 -*-
# AUTHOR: RaNaN, mkaay

from threading import RLock
from .event_manager import InsertEvent, ReloadAllEvent, RemoveEvent, UpdateEvent
from ..utils import lock
from ..datatypes import Destination


class FileManager(object):
    """
    Handles all request made to obtain information, modify status or other request for
    links or packages.
    """

    def __init__(self, core):
        """
        Constructor.
        """
        self.pyload = core
        self._ = core._

        # translations
        self.statusMsg = [
            self._("finished"),
            self._("offline"),
            self._("online"),
            self._("queued"),
            self._("skipped"),
            self._("waiting"),
            self._("temp. offline"),
            self._("starting"),
            self._("failed"),
            self._("aborted"),
            self._("decrypting"),
            self._("custom"),
            self._("downloading"),
            self._("processing"),
            self._("unknown"),
        ]

        # TODO: purge the cache
        self.cache = {}  #: holds instances for files
        self.packageCache = {}  #: same for packages

        self.jobCache = {}

        self.lock = RLock()  # TODO: should be a Lock w/o R
        # self.lock._Verbose__verbose = True

        self.filecount = -1  #: if an invalid value is set get current value from db
        self.queuecount = -1  #: number of package to be loaded
        self.unchanged = False  #: determines if any changes was made since last call

    def change(func):
        def new(*args):
            args[0].unchanged = False
            args[0].filecount = -1
            args[0].queuecount = -1
            args[0].jobCache = {}
            return func(*args)

        return new

    # ----------------------------------------------------------------------
    def save(self):
        """
        saves all data to backend.
        """
        self.pyload.db.commit()

    # ----------------------------------------------------------------------
    def syncSave(self):
        """
        saves all data to backend and waits until all data are written.
        """
        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            pyfile.sync()

        pypacks = self.packageCache.values()
        for pypack in pypacks:
            pypack.sync()

        self.pyload.db.syncSave()

    @lock
    def getCompleteData(self, queue=Destination.QUEUE):
        """
        gets a complete data representation.
        """
        queue = queue.value
        data = self.pyload.db.getAllLinks(queue)
        packs = self.pyload.db.getAllPackages(queue)

        data.update((x.id, x.toDbDict()[x.id]) for x in self.cache.values())

        for x in self.packageCache.values():
            if x.queue != queue or x.id not in packs:
                continue
            packs[x.id].update(x.toDict()[x.id])

        for key, value in data.items():
            if value["package"] in packs:
                packs[value["package"]]["links"][key] = value

        return packs

    @lock
    def getInfoData(self, queue=Destination.QUEUE):
        """
        gets a data representation without links.
        """
        queue = queue.value
        packs = self.pyload.db.getAllPackages(queue)
        for x in self.packageCache.values():
            if x.queue != queue or x.id not in packs:
                continue
            packs[x.id].update(x.toDict()[x.id])

        return packs

    @lock
    @change
    def addLinks(self, urls, package):
        """
        adds links.
        """
        self.pyload.addonManager.dispatchEvent("linksAdded", urls, package)

        data = self.pyload.pluginManager.parseUrls(urls)

        self.pyload.db.addLinks(data, package)
        self.pyload.threadManager.createInfoThread(data, package)

        # TODO: change from reloadAll event to package update event
        self.pyload.eventManager.addEvent(ReloadAllEvent("collector"))

    # ----------------------------------------------------------------------
    @lock
    @change
    def addPackage(self, name, folder, queue=Destination.QUEUE):
        """
        adds a package, default to link collector.
        """
        lastID = self.pyload.db.addPackage(name, folder, queue.value)
        p = self.pyload.db.getPackage(lastID)
        e = InsertEvent(
            "pack",
            lastID,
            p.order,
            "collector" if queue is Destination.COLLECTOR else "queue",
        )
        self.pyload.eventManager.addEvent(e)
        return lastID

    # ----------------------------------------------------------------------
    @lock
    @change
    def deletePackage(self, id):
        """
        delete package and all contained links.
        """
        p = self.getPackage(id)
        if not p:
            if id in self.packageCache:
                del self.packageCache[id]
            return

        oldorder = p.order
        queue = p.queue

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == id:
                pyfile.abortDownload()
                pyfile.release()

        self.pyload.db.deletePackage(p)
        self.pyload.eventManager.addEvent(e)
        self.pyload.addonManager.dispatchEvent("packageDeleted", id)

        if id in self.packageCache:
            del self.packageCache[id]

        packs = self.packageCache.values()
        for pack in packs:
            if pack.queue == queue and pack.order > oldorder:
                pack.order -= 1
                pack.notifyChange()

    # ----------------------------------------------------------------------
    @lock
    @change
    def deleteLink(self, id):
        """
        deletes links.
        """
        f = self.getFile(id)
        if not f:
            return None

        pid = f.packageid
        e = RemoveEvent("file", id, "collector" if not f.package().queue else "queue")

        oldorder = f.order

        if id in self.pyload.threadManager.processingIds():
            self.cache[id].abortDownload()

        if id in self.cache:
            del self.cache[id]

        self.pyload.db.deleteLink(f)

        self.pyload.eventManager.addEvent(e)

        p = self.getPackage(pid)
        if not len(p.getChildren()):
            p.delete()

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == pid and pyfile.order > oldorder:
                pyfile.order -= 1
                pyfile.notifyChange()

    # ----------------------------------------------------------------------
    def releaseLink(self, id):
        """
        removes pyfile from cache.
        """
        if id in self.cache:
            del self.cache[id]

    # ----------------------------------------------------------------------
    def releasePackage(self, id):
        """
        removes package from cache.
        """
        if id in self.packageCache:
            del self.packageCache[id]

    # ----------------------------------------------------------------------
    def updateLink(self, pyfile):
        """
        updates link.
        """
        self.pyload.db.updateLink(pyfile)

        e = UpdateEvent(
            "file", pyfile.id, "collector" if not pyfile.package().queue else "queue"
        )
        self.pyload.eventManager.addEvent(e)

    # ----------------------------------------------------------------------
    def updatePackage(self, pypack):
        """
        updates a package.
        """
        self.pyload.db.updatePackage(pypack)

        e = UpdateEvent("pack", pypack.id, "collector" if not pypack.queue else "queue")
        self.pyload.eventManager.addEvent(e)

    # ----------------------------------------------------------------------
    def getPackage(self, id):
        """
        return package instance.
        """
        if id in self.packageCache:
            return self.packageCache[id]
        else:
            return self.pyload.db.getPackage(id)

    # ----------------------------------------------------------------------
    def getPackageData(self, id):
        """
        returns dict with package information.
        """
        pack = self.getPackage(id)

        if not pack:
            return None

        pack = pack.toDict()[id]

        data = self.pyload.db.getPackageData(id)

        tmplist = []

        cache = self.cache.values()
        for x in cache:
            if int(x.toDbDict()[x.id]["package"]) == int(id):
                tmplist.append((x.id, x.toDbDict()[x.id]))
        data.update(tmplist)

        pack["links"] = data

        return pack

    # ----------------------------------------------------------------------
    def getFileData(self, id):
        """
        returns dict with file information.
        """
        if id in self.cache:
            return self.cache[id].toDbDict()

        return self.pyload.db.getLinkData(id)

    # ----------------------------------------------------------------------
    def getFile(self, id):
        """
        returns pyfile instance.
        """
        if id in self.cache:
            return self.cache[id]
        else:
            return self.pyload.db.getFile(id)

    # ----------------------------------------------------------------------
    @lock
    def getJob(self, occ):
        """
        get suitable job.
        """
        # TODO: clean mess
        # TODO: improve selection of valid jobs

        if occ in self.jobCache:
            if self.jobCache[occ]:
                id = self.jobCache[occ].pop()
                if id == "empty":
                    pyfile = None
                    self.jobCache[occ].append("empty")
                else:
                    pyfile = self.getFile(id)
            else:
                jobs = self.pyload.db.getJob(occ)
                jobs.reverse()
                if not jobs:
                    self.jobCache[occ].append("empty")
                    pyfile = None
                else:
                    self.jobCache[occ].extend(jobs)
                    pyfile = self.getFile(self.jobCache[occ].pop())

        else:
            self.jobCache = {}  #: better not caching to much
            jobs = self.pyload.db.getJob(occ)
            jobs.reverse()
            self.jobCache[occ] = jobs

            if not jobs:
                self.jobCache[occ].append("empty")
                pyfile = None
            else:
                pyfile = self.getFile(self.jobCache[occ].pop())

            # TODO: maybe the new job has to be approved...

        # pyfile = self.getFile(self.jobCache[occ].pop())
        return pyfile

    @lock
    def getDecryptJob(self):
        """
        return job for decrypting.
        """
        if "decrypt" in self.jobCache:
            return None

        plugins = list(self.pyload.pluginManager.crypterPlugins.keys()) + list(
            self.pyload.pluginManager.containerPlugins.keys()
        )
        plugins = str(tuple(plugins))

        jobs = self.pyload.db.getPluginJob(plugins)
        if jobs:
            return self.getFile(jobs[0])
        else:
            self.jobCache["decrypt"] = "empty"
            return None

    def getFileCount(self):
        """
        returns number of files.
        """
        if self.filecount == -1:
            self.filecount = self.pyload.db.filecount(1)

        return self.filecount

    def getQueueCount(self, force=False):
        """
        number of files that have to be processed.
        """
        if self.queuecount == -1 or force:
            self.queuecount = self.pyload.db.queuecount(1)

        return self.queuecount

    def checkAllLinksFinished(self):
        """
        checks if all files are finished and dispatch event.
        """
        if not self.getQueueCount(True):
            self.pyload.addonManager.dispatchEvent("allDownloadsFinished")
            self.pyload.log.debug("All downloads finished")
            return True

        return False

    def checkAllLinksProcessed(self, fid):
        """
        checks if all files was processed and pyload would idle now, needs fid which
        will be ignored when counting.
        """
        # reset count so statistic will update (this is called when dl was processed)
        self.resetCount()

        if not self.pyload.db.processcount(1, fid):
            self.pyload.addonManager.dispatchEvent("allDownloadsProcessed")
            self.pyload.log.debug("All downloads processed")
            return True

        return False

    def resetCount(self):
        self.queuecount = -1

    @lock
    @change
    def restartPackage(self, id):
        """
        restart package.
        """
        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == id:
                self.restartFile(pyfile.id)

        self.pyload.db.restartPackage(id)

        if id in self.packageCache:
            self.packageCache[id].setFinished = False

        e = UpdateEvent(
            "pack", id, "collector" if not self.getPackage(id).queue else "queue"
        )
        self.pyload.eventManager.addEvent(e)

    @lock
    @change
    def restartFile(self, id):
        """
        restart file.
        """
        if id in self.cache:
            self.cache[id].status = 3
            self.cache[id].name = self.cache[id].url
            self.cache[id].error = ""
            self.cache[id].abortDownload()

        self.pyload.db.restartFile(id)

        e = UpdateEvent(
            "file", id, "collector" if not self.getFile(id).package().queue else "queue"
        )
        self.pyload.eventManager.addEvent(e)

    @lock
    @change
    def setPackageLocation(self, id, queue):
        """
        push package to queue.
        """
        queue = queue.value
        p = self.pyload.db.getPackage(id)
        oldorder = p.order

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")
        self.pyload.eventManager.addEvent(e)

        self.pyload.db.clearPackageOrder(p)

        p = self.pyload.db.getPackage(id)

        p.queue = queue
        self.pyload.db.updatePackage(p)

        self.pyload.db.reorderPackage(p, -1, True)

        packs = self.packageCache.values()
        for pack in packs:
            if pack.queue != queue and pack.order > oldorder:
                pack.order -= 1
                pack.notifyChange()

        self.pyload.db.commit()
        self.releasePackage(id)
        p = self.getPackage(id)

        e = InsertEvent("pack", id, p.order, "collector" if not p.queue else "queue")
        self.pyload.eventManager.addEvent(e)

    @lock
    @change
    def reorderPackage(self, id, position):
        p = self.getPackage(id)

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")
        self.pyload.eventManager.addEvent(e)
        self.pyload.db.reorderPackage(p, position)

        packs = self.packageCache.values()
        for pack in packs:
            if pack.queue != p.queue or pack.order < 0 or pack == p:
                continue
            if p.order > position:
                if pack.order >= position and pack.order < p.order:
                    pack.order += 1
                    pack.notifyChange()
            elif p.order < position:
                if pack.order <= position and pack.order > p.order:
                    pack.order -= 1
                    pack.notifyChange()

        p.order = position
        self.pyload.db.commit()

        e = InsertEvent("pack", id, position, "collector" if not p.queue else "queue")
        self.pyload.eventManager.addEvent(e)

    @lock
    @change
    def reorderFile(self, id, position):
        f = self.getFileData(id)
        f = f[id]

        e = RemoveEvent(
            "file",
            id,
            "collector" if not self.getPackage(f["package"]).queue else "queue",
        )
        self.pyload.eventManager.addEvent(e)

        self.pyload.db.reorderLink(f, position)

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid != f["package"] or pyfile.order < 0:
                continue
            if f["order"] > position:
                if pyfile.order >= position and pyfile.order < f["order"]:
                    pyfile.order += 1
                    pyfile.notifyChange()
            elif f["order"] < position:
                if pyfile.order <= position and pyfile.order > f["order"]:
                    pyfile.order -= 1
                    pyfile.notifyChange()

        if id in self.cache:
            self.cache[id].order = position

        self.pyload.db.commit()

        e = InsertEvent(
            "file",
            id,
            position,
            "collector" if not self.getPackage(f["package"]).queue else "queue",
        )
        self.pyload.eventManager.addEvent(e)

    @change
    def updateFileInfo(self, data, pid):
        """
        updates file info (name, size, status, url)
        """
        self.pyload.db.updateLinkInfo(data)
        e = UpdateEvent(
            "pack", pid, "collector" if not self.getPackage(pid).queue else "queue"
        )
        self.pyload.eventManager.addEvent(e)

    def checkPackageFinished(self, pyfile):
        """
        checks if package is finished and calls addonManager.
        """
        ids = self.pyload.db.getUnfinished(pyfile.packageid)
        if not ids or (pyfile.id in ids and len(ids) == 1):
            if not pyfile.package().setFinished:
                self.pyload.log.info(
                    self._("Package finished: {}").format(pyfile.package().name)
                )
                self.pyload.addonManager.packageFinished(pyfile.package())
                pyfile.package().setFinished = True

    def reCheckPackage(self, pid):
        """
        recheck links in package.
        """
        data = self.pyload.db.getPackageData(pid)

        urls = []

        for pyfile in data.values():
            if pyfile["status"] not in (0, 12, 13):
                urls.append((pyfile["url"], pyfile["plugin"]))

        self.pyload.threadManager.createInfoThread(urls, pid)

    @lock
    @change
    def deleteFinishedLinks(self):
        """
        deletes finished links and packages, return deleted packages.
        """
        old_packs = self.getInfoData(0)
        old_packs.update(self.getInfoData(1))

        self.pyload.db.deleteFinished()

        new_packs = self.pyload.db.getAllPackages(0)
        new_packs.update(self.pyload.db.getAllPackages(1))
        # get new packages only from db

        deleted = []
        for id in old_packs.keys():
            if id not in new_packs:
                deleted.append(id)
                self.deletePackage(int(id))

        return deleted

    @lock
    @change
    def restartFailed(self):
        """
        restart all failed links.
        """
        self.pyload.db.restartFailed()
