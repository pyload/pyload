# -*- coding: utf-8 -*-
# AUTHOR: RaNaN, mkaay

from builtins import object, range, str, zip
from threading import RLock

from ..datatypes.pyfile import PyFile
from ..datatypes.pypackage import PyPackage
from ..managers.event_manager import (
    InsertEvent,
    ReloadAllEvent,
    RemoveEvent,
    UpdateEvent,
)
from ..utils import formatSize, lock
from .database_thread import DatabaseThread, style


class FileHandler(object):
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

        self.cache = {}  #: holds instances for files
        self.packageCache = {}  #: same for packages
        # TODO: purge the cache

        self.jobCache = {}

        self.lock = RLock()  # TODO: should be a Lock w/o R
        # self.lock._Verbose__verbose = True

        self.filecount = -1  #: if an invalid value is set get current value from db
        self.queuecount = -1  #: number of package to be loaded
        self.unchanged = False  #: determines if any changes was made since last call

        self.db = self.pyload.db

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
        self.db.commit()

    # ----------------------------------------------------------------------
    def syncSave(self):
        """
        saves all data to backend and waits until all data are written.
        """
        pyfiles = list(self.cache.values())
        for pyfile in pyfiles:
            pyfile.sync()

        pypacks = list(self.packageCache.values())
        for pypack in pypacks:
            pypack.sync()

        self.db.syncSave()

    @lock
    def getCompleteData(self, queue=1):
        """
        gets a complete data representation.
        """
        data = self.db.getAllLinks(queue)
        packs = self.db.getAllPackages(queue)

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
    def getInfoData(self, queue=1):
        """
        gets a data representation without links.
        """
        packs = self.db.getAllPackages(queue)
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

        self.db.addLinks(data, package)
        self.pyload.threadManager.createInfoThread(data, package)

        # TODO: change from reloadAll event to package update event
        self.pyload.eventManager.addEvent(ReloadAllEvent("collector"))

    # ----------------------------------------------------------------------
    @lock
    @change
    def addPackage(self, name, folder, queue=0):
        """
        adds a package, default to link collector.
        """
        lastID = self.db.addPackage(name, folder, queue)
        p = self.db.getPackage(lastID)
        e = InsertEvent("pack", lastID, p.order, "collector" if not queue else "queue")
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

        pyfiles = list(self.cache.values())

        for pyfile in pyfiles:
            if pyfile.packageid == id:
                pyfile.abortDownload()
                pyfile.release()

        self.db.deletePackage(p)
        self.pyload.eventManager.addEvent(e)
        self.pyload.addonManager.dispatchEvent("packageDeleted", id)

        if id in self.packageCache:
            del self.packageCache[id]

        packs = list(self.packageCache.values())
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

        self.db.deleteLink(f)

        self.pyload.eventManager.addEvent(e)

        p = self.getPackage(pid)
        if not len(p.getChildren()):
            p.delete()

        pyfiles = list(self.cache.values())
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
        self.db.updateLink(pyfile)

        e = UpdateEvent(
            "file", pyfile.id, "collector" if not pyfile.package().queue else "queue"
        )
        self.pyload.eventManager.addEvent(e)

    # ----------------------------------------------------------------------
    def updatePackage(self, pypack):
        """
        updates a package.
        """
        self.db.updatePackage(pypack)

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
            return self.db.getPackage(id)

    # ----------------------------------------------------------------------
    def getPackageData(self, id):
        """
        returns dict with package information.
        """
        pack = self.getPackage(id)

        if not pack:
            return None

        pack = pack.toDict()[id]

        data = self.db.getPackageData(id)

        tmplist = []

        cache = list(self.cache.values())
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

        return self.db.getLinkData(id)

    # ----------------------------------------------------------------------
    def getFile(self, id):
        """
        returns pyfile instance.
        """
        if id in self.cache:
            return self.cache[id]
        else:
            return self.db.getFile(id)

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
                jobs = self.db.getJob(occ)
                jobs.reverse()
                if not jobs:
                    self.jobCache[occ].append("empty")
                    pyfile = None
                else:
                    self.jobCache[occ].extend(jobs)
                    pyfile = self.getFile(self.jobCache[occ].pop())

        else:
            self.jobCache = {}  #: better not caching to much
            jobs = self.db.getJob(occ)
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

        jobs = self.db.getPluginJob(plugins)
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
            self.filecount = self.db.filecount(1)

        return self.filecount

    def getQueueCount(self, force=False):
        """
        number of files that have to be processed.
        """
        if self.queuecount == -1 or force:
            self.queuecount = self.db.queuecount(1)

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

        if not self.db.processcount(1, fid):
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
        pyfiles = list(self.cache.values())
        for pyfile in pyfiles:
            if pyfile.packageid == id:
                self.restartFile(pyfile.id)

        self.db.restartPackage(id)

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

        self.db.restartFile(id)

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
        p = self.db.getPackage(id)
        oldorder = p.order

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")
        self.pyload.eventManager.addEvent(e)

        self.db.clearPackageOrder(p)

        p = self.db.getPackage(id)

        p.queue = queue
        self.db.updatePackage(p)

        self.db.reorderPackage(p, -1, True)

        packs = list(self.packageCache.values())
        for pack in packs:
            if pack.queue != queue and pack.order > oldorder:
                pack.order -= 1
                pack.notifyChange()

        self.db.commit()
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
        self.db.reorderPackage(p, position)

        packs = list(self.packageCache.values())
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
        self.db.commit()

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

        self.db.reorderLink(f, position)

        pyfiles = list(self.cache.values())
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

        self.db.commit()

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
        self.db.updateLinkInfo(data)
        e = UpdateEvent(
            "pack", pid, "collector" if not self.getPackage(pid).queue else "queue"
        )
        self.pyload.eventManager.addEvent(e)

    def checkPackageFinished(self, pyfile):
        """
        checks if package is finished and calls addonManager.
        """
        ids = self.db.getUnfinished(pyfile.packageid)
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
        data = self.db.getPackageData(pid)

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

        self.db.deleteFinished()

        new_packs = self.db.getAllPackages(0)
        new_packs.update(self.db.getAllPackages(1))
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
        self.db.restartFailed()


class FileMethods(object):
    @style.queue
    def filecount(self, queue):
        """
        returns number of files in queue.
        """
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=?",
            (queue,),
        )
        return self.c.fetchone()[0]

    @style.queue
    def queuecount(self, queue):
        """
        number of files in queue not finished yet.
        """
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? AND l.status NOT IN (0,4)",
            (queue,),
        )
        return self.c.fetchone()[0]

    @style.queue
    def processcount(self, queue, fid):
        """
        number of files which have to be proccessed.
        """
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? AND l.status IN (2,3,5,7,12) AND l.id != ?",
            (queue, str(fid)),
        )
        return self.c.fetchone()[0]

    @style.inner
    def _nextPackageOrder(self, queue=0):
        self.c.execute("SELECT MAX(packageorder) FROM packages WHERE queue=?", (queue,))
        max = self.c.fetchone()[0]
        if max is not None:
            return max + 1
        else:
            return 0

    @style.inner
    def _nextFileOrder(self, package):
        self.c.execute("SELECT MAX(linkorder) FROM links WHERE package=?", (package,))
        max = self.c.fetchone()[0]
        if max is not None:
            return max + 1
        else:
            return 0

    @style.queue
    def addLink(self, url, name, plugin, package):
        order = self._nextFileOrder(package)
        self.c.execute(
            "INSERT INTO links(url, name, plugin, package, linkorder) VALUES(?,?,?,?,?)",
            (url, name, plugin, package, order),
        )
        return self.c.lastrowid

    @style.queue
    def addLinks(self, links, package):
        """
        links is a list of tupels (url,plugin)
        """
        order = self._nextFileOrder(package)
        orders = [order + x for x in range(len(links))]
        links = [(x[0], x[0], x[1], package, o) for x, o in zip(links, orders)]
        self.c.executemany(
            "INSERT INTO links(url, name, plugin, package, linkorder) VALUES(?,?,?,?,?)",
            links,
        )

    @style.queue
    def addPackage(self, name, folder, queue):
        order = self._nextPackageOrder(queue)
        self.c.execute(
            "INSERT INTO packages(name, folder, queue, packageorder) VALUES(?,?,?,?)",
            (name, folder, queue, order),
        )
        return self.c.lastrowid

    @style.queue
    def deletePackage(self, p):
        self.c.execute("DELETE FROM links WHERE package=?", (str(p.id),))
        self.c.execute("DELETE FROM packages WHERE id=?", (str(p.id),))
        self.c.execute(
            "UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > ? AND queue=?",
            (p.order, p.queue),
        )

    @style.queue
    def deleteLink(self, f):
        self.c.execute("DELETE FROM links WHERE id=?", (str(f.id),))
        self.c.execute(
            "UPDATE links SET linkorder=linkorder-1 WHERE linkorder > ? AND package=?",
            (f.order, str(f.packageid)),
        )

    @style.queue
    def getAllLinks(self, q):
        """
        return information about all links in queue q.

        q0 queue
        q1 collector

        format:

        {
            id: {'name': name, ... 'package': id }, ...
        }
        """
        self.c.execute(
            "SELECT l.id,l.url,l.name,l.size,l.status,l.error,l.plugin,l.package,l.linkorder FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? ORDER BY l.linkorder",
            (q,),
        )
        data = {}
        for r in self.c:
            data[r[0]] = {
                "id": r[0],
                "url": r[1],
                "name": r[2],
                "size": r[3],
                "format_size": formatSize(r[3]),
                "status": r[4],
                "statusmsg": self.m.statusMsg[r[4]],
                "error": r[5],
                "plugin": r[6],
                "package": r[7],
                "order": r[8],
            }

        return data

    @style.queue
    def getAllPackages(self, q):
        """
        return information about packages in queue q (only useful in get all data)

        q0 queue
        q1 collector

        format:

        {
            id: {'name': name ... 'links': {} }, ...
        }
        """
        self.c.execute(
            "SELECT p.id, p.name, p.folder, p.site, p.password, p.queue, p.packageorder, s.sizetotal, s.sizedone, s.linksdone, s.linkstotal \
            FROM packages p JOIN pstats s ON p.id = s.id \
            WHERE p.queue=? ORDER BY p.packageorder",
            str(q),
        )

        data = {}
        for r in self.c:
            data[r[0]] = {
                "id": r[0],
                "name": r[1],
                "folder": r[2],
                "site": r[3],
                "password": r[4],
                "queue": r[5],
                "order": r[6],
                "sizetotal": int(r[7]),
                "sizedone": r[8] if r[8] else 0,  #: these can be None
                "linksdone": r[9] if r[9] else 0,
                "linkstotal": r[10],
                "links": {},
            }

        return data

    @style.queue
    def getLinkData(self, id):
        """
        get link information as dict.
        """
        self.c.execute(
            "SELECT id,url,name,size,status,error,plugin,package,linkorder FROM links WHERE id=?",
            (str(id),),
        )
        data = {}
        r = self.c.fetchone()
        if not r:
            return None
        data[r[0]] = {
            "id": r[0],
            "url": r[1],
            "name": r[2],
            "size": r[3],
            "format_size": formatSize(r[3]),
            "status": r[4],
            "statusmsg": self.m.statusMsg[r[4]],
            "error": r[5],
            "plugin": r[6],
            "package": r[7],
            "order": r[8],
        }

        return data

    @style.queue
    def getPackageData(self, id):
        """
        get data about links for a package.
        """
        self.c.execute(
            "SELECT id,url,name,size,status,error,plugin,package,linkorder FROM links WHERE package=? ORDER BY linkorder",
            (str(id),),
        )

        data = {}
        for r in self.c:
            data[r[0]] = {
                "id": r[0],
                "url": r[1],
                "name": r[2],
                "size": r[3],
                "format_size": formatSize(r[3]),
                "status": r[4],
                "statusmsg": self.m.statusMsg[r[4]],
                "error": r[5],
                "plugin": r[6],
                "package": r[7],
                "order": r[8],
            }

        return data

    @style.async_
    def updateLink(self, f):
        self.c.execute(
            "UPDATE links SET url=?,name=?,size=?,status=?,error=?,package=? WHERE id=?",
            (f.url, f.name, f.size, f.status, f.error, str(f.packageid), str(f.id)),
        )

    @style.queue
    def updatePackage(self, p):
        self.c.execute(
            "UPDATE packages SET name=?,folder=?,site=?,password=?,queue=? WHERE id=?",
            (p.name, p.folder, p.site, p.password, p.queue, str(p.id)),
        )

    @style.queue
    def updateLinkInfo(self, data):
        """
        data is list of tupels (name, size, status, url)
        """
        self.c.executemany(
            "UPDATE links SET name=?, size=?, status=? WHERE url=? AND status IN (1,2,3,14)",
            data,
        )
        ids = []
        statuses = "','".join(x[3] for x in data)
        self.c.execute(f"SELECT id FROM links WHERE url IN ('{statuses}')")
        for r in self.c:
            ids.append(int(r[0]))
        return ids

    @style.queue
    def reorderPackage(self, p, position, noMove=False):
        if position == -1:
            position = self._nextPackageOrder(p.queue)
        if not noMove:
            if p.order > position:
                self.c.execute(
                    "UPDATE packages SET packageorder=packageorder+1 WHERE packageorder >= ? AND packageorder < ? AND queue=? AND packageorder >= 0",
                    (position, p.order, p.queue),
                )
            elif p.order < position:
                self.c.execute(
                    "UPDATE packages SET packageorder=packageorder-1 WHERE packageorder <= ? AND packageorder > ? AND queue=? AND packageorder >= 0",
                    (position, p.order, p.queue),
                )

        self.c.execute(
            "UPDATE packages SET packageorder=? WHERE id=?", (position, str(p.id))
        )

    @style.queue
    def reorderLink(self, f, position):
        """
        reorder link with f as dict for pyfile.
        """
        if f["order"] > position:
            self.c.execute(
                "UPDATE links SET linkorder=linkorder+1 WHERE linkorder >= ? AND linkorder < ? AND package=?",
                (position, f["order"], f["package"]),
            )
        elif f["order"] < position:
            self.c.execute(
                "UPDATE links SET linkorder=linkorder-1 WHERE linkorder <= ? AND linkorder > ? AND package=?",
                (position, f["order"], f["package"]),
            )

        self.c.execute("UPDATE links SET linkorder=? WHERE id=?", (position, f["id"]))

    @style.queue
    def clearPackageOrder(self, p):
        self.c.execute("UPDATE packages SET packageorder=? WHERE id=?", (-1, str(p.id)))
        self.c.execute(
            "UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > ? AND queue=? AND id != ?",
            (p.order, p.queue, str(p.id)),
        )

    @style.async_
    def restartFile(self, id):
        self.c.execute('UPDATE links SET status=3,error="" WHERE id=?', (str(id),))

    @style.async_
    def restartPackage(self, id):
        self.c.execute("UPDATE links SET status=3 WHERE package=?", (str(id),))

    @style.queue
    def getPackage(self, id):
        """
        return package instance from id.
        """
        self.c.execute(
            "SELECT name,folder,site,password,queue,packageorder FROM packages WHERE id=?",
            (str(id),),
        )
        r = self.c.fetchone()
        if not r:
            return None
        return PyPackage(self.m, id, *r)

    # ----------------------------------------------------------------------
    @style.queue
    def getFile(self, id):
        """
        return link instance from id.
        """
        self.c.execute(
            "SELECT url, name, size, status, error, plugin, package, linkorder FROM links WHERE id=?",
            (str(id),),
        )
        r = self.c.fetchone()
        if not r:
            return None
        return PyFile(self.m, id, *r)

    @style.queue
    def getJob(self, occ):
        """
        return pyfile ids, which are suitable for download and dont use a occupied
        plugin.
        """
        # TODO: improve this hardcoded method
        # plugins which are processed in collector
        pre = "('DLC', 'LinkList', 'SerienjunkiesOrg', 'CCF', 'RSDF')"

        cmd = "("
        for i, item in enumerate(occ):
            if i:
                cmd += ", "
            cmd += f"'{item}'"

        cmd += ")"
        cmd = f"SELECT l.id FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE ((p.queue=1 AND l.plugin NOT IN {cmd}) OR l.plugin IN {pre}) AND l.status IN (2,3,14) ORDER BY p.packageorder ASC, l.linkorder ASC LIMIT 5"

        self.c.execute(cmd)  #: very bad!

        return [x[0] for x in self.c]

    @style.queue
    def getPluginJob(self, plugins):
        """
        returns pyfile ids with suited plugins.
        """
        cmd = f"SELECT l.id FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE l.plugin IN {plugins} AND l.status IN (2,3,14) ORDER BY p.packageorder ASC, l.linkorder ASC LIMIT 5"

        self.c.execute(cmd)  #: very bad!

        return [x[0] for x in self.c]

    @style.queue
    def getUnfinished(self, pid):
        """
        return list of max length 3 ids with pyfiles in package not finished or
        processed.
        """
        self.c.execute(
            "SELECT id FROM links WHERE package=? AND status NOT IN (0, 4, 13) LIMIT 3",
            (str(pid),),
        )
        return [r[0] for r in self.c]

    @style.queue
    def deleteFinished(self):
        self.c.execute("DELETE FROM links WHERE status IN (0,4)")
        self.c.execute(
            "DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE packages.id=links.package)"
        )

    @style.queue
    def restartFailed(self):
        self.c.execute("UPDATE links SET status=3,error='' WHERE status IN (6, 8, 9)")

    @style.queue
    def findDuplicates(self, id, folder, filename):
        """
        checks if filename exists with different id and same package.
        """
        self.c.execute(
            "SELECT l.plugin FROM links as l INNER JOIN packages as p ON l.package=p.id AND p.folder=? WHERE l.id!=? AND l.status=0 AND l.name=?",
            (folder, id, filename),
        )
        return self.c.fetchone()

    @style.queue
    def purgeLinks(self):
        self.c.execute("DELETE FROM links;")
        self.c.execute("DELETE FROM packages;")


DatabaseThread.registerSub(FileMethods)
