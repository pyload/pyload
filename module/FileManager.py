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
from threading import RLock

from module.utils import lock

from Api import PackageStatus, DownloadStatus as DS, TreeCollection, PackageDoesNotExists
from datatypes.PyFile import PyFile
from datatypes.PyPackage import PyPackage, RootPackage

# invalidates the cache
def invalidate(func):
    def new(*args):
        args[0].filecount = -1
        args[0].downloadcount = -1
        args[0].queuecount = -1
        args[0].jobCache = {}
        return func(*args)

    return new

# TODO: needs to be replaced later
OWNER = 0

class FileManager:
    """Handles all request made to obtain information,
    modify status or other request for links or packages"""

    ROOT_PACKAGE = -1

    def __init__(self, core):
        """Constructor"""
        self.core = core
        self.evm = core.eventManager

        # translations
        self.statusMsg = [_("none"), _("offline"), _("online"), _("queued"), _("paused"),
                          _("finished"), _("skipped"), _("failed"), _("starting"),
                          _("waiting"), _("downloading"), _("temp. offline"), _("aborted"),
                          _("decrypting"), _("processing"), _("custom"), _("unknown")]

        self.files = {} # holds instances for files
        self.packages = {}  # same for packages

        self.jobCache = {}

        # locking the cache, db is already locked implicit
        self.lock = RLock()
        #self.lock._Verbose__verbose = True

        self.filecount = -1 # if an invalid value is set get current value from db
        self.downloadcount = -1 # number of downloads
        self.queuecount = -1 # number of package to be loaded

        self.db = self.core.db

    def save(self):
        """saves all data to backend"""
        self.db.commit()

    @lock
    def syncSave(self):
        """saves all data to backend and waits until all data are written"""
        for pyfile in self.files.values():
            pyfile.sync()

        for pypack in self.packages.values():
            pypack.sync()

        self.db.syncSave()

    def cachedFiles(self):
        return self.files.values()

    def cachedPackages(self):
        return self.packages.values()

    def getCollector(self):
        pass

    @invalidate
    def addLinks(self, data, package):
        """Add links, data = (plugin, url) tuple. Internal method should use API."""
        self.db.addLinks(data, package, OWNER)
        self.evm.dispatchEvent("packageUpdated", package)


    @invalidate
    def addPackage(self, name, folder, root, password, site, comment, paused):
        """Adds a package to database"""
        pid = self.db.addPackage(name, folder, root, password, site, comment,
            PackageStatus.Paused if paused else PackageStatus.Ok, OWNER)
        p = self.db.getPackageInfo(pid)

        self.evm.dispatchEvent("packageInserted", pid, p.root, p.packageorder)
        return pid


    @lock
    def getPackage(self, pid):
        """return package instance"""
        if pid == self.ROOT_PACKAGE:
            return RootPackage(self, OWNER)
        elif pid in self.packages:
            pack = self.packages[pid]
            pack.timestamp = time()
            return pack
        else:
            info = self.db.getPackageInfo(pid, False)
            if not info: return None

            pack = PyPackage.fromInfoData(self, info)
            self.packages[pid] = pack

            return pack

    @lock
    def getPackageInfo(self, pid):
        """returns dict with package information"""
        if pid == self.ROOT_PACKAGE:
            pack = RootPackage(self, OWNER).toInfoData()
        elif pid in self.packages:
            pack = self.packages[pid].toInfoData()
            pack.stats = self.db.getStatsForPackage(pid)
        else:
            pack = self.db.getPackageInfo(pid)

        if not pack: return None

        # todo: what does this todo mean?!
        #todo: fill child packs and files
        packs = self.db.getAllPackages(root=pid)
        if pid in packs: del packs[pid]
        pack.pids = packs.keys()

        files = self.db.getAllFiles(package=pid)
        pack.fids = files.keys()

        return pack

    @lock
    def getFile(self, fid):
        """returns pyfile instance"""
        if fid in self.files:
            return self.files[fid]
        else:
            info = self.db.getFileInfo(fid)
            if not info: return None

            f = PyFile.fromInfoData(self, info)
            self.files[fid] = f
            return f

    @lock
    def getFileInfo(self, fid):
        """returns dict with file information"""
        if fid in self.files:
            return self.files[fid].toInfoData()

        return self.db.getFileInfo(fid)

    @lock
    def getTree(self, pid, full, state):
        """  return a TreeCollection and fill the info data of containing packages.
             optional filter only unfnished files
        """
        view = TreeCollection(pid)

        # for depth=1, we don't need to retrieve all files/packages
        root = pid if not full else None

        packs = self.db.getAllPackages(root)
        files = self.db.getAllFiles(package=root, state=state)

        # updating from cache
        for fid, f in self.files.iteritems():
            if fid in files:
                files[fid] = f.toInfoData()

        # foreign pid, don't overwrite local pid !
        for fpid, p in self.packages.iteritems():
            if fpid in packs:
                # copy the stats data
                stats = packs[fpid].stats
                packs[fpid] = p.toInfoData()
                packs[fpid].stats = stats

        # root package is not in database, create an instance
        if pid == self.ROOT_PACKAGE:
            view.root = RootPackage(self, OWNER).toInfoData()
            packs[self.ROOT_PACKAGE] = view.root
        elif pid in packs:
            view.root = packs[pid]
        else: # package does not exists
            return view

        # linear traversal over all data
        for fpid, p in packs.iteritems():
            if p.fids is None: p.fids = []
            if p.pids is None: p.pids = []

            root = packs.get(p.root, None)
            if root:
                if root.pids is None: root.pids = []
                root.pids.append(fpid)

        for fid, f in files.iteritems():
            p = packs.get(f.package, None)
            if p: p.fids.append(fid)


        # cutting of tree is not good in runtime, only saves bandwidth
        # need to remove some entries
        if full and pid > -1:
            keep = []
            queue = [pid]
            while queue:
                fpid = queue.pop()
                keep.append(fpid)
                queue.extend(packs[fpid].pids)

            # now remove unneeded data
            for fpid in packs.keys():
                if fpid not in keep:
                    del packs[fpid]

            for fid, f in files.items():
                if f.package not in keep:
                    del files[fid]

        #remove root
        del packs[pid]
        view.files = files
        view.packages = packs

        return view


    @lock
    def getJob(self, occ):
        """get suitable job"""

        #TODO needs to be approved for new database
        #TODO clean mess
        #TODO improve selection of valid jobs

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
            self.jobCache = {} #better not caching to much
            jobs = self.db.getJob(occ)
            jobs.reverse()
            self.jobCache[occ] = jobs

            if not jobs:
                self.jobCache[occ].append("empty")
                pyfile = None
            else:
                pyfile = self.getFile(self.jobCache[occ].pop())


        return pyfile


    def getFileCount(self):
        """returns number of files"""

        if self.filecount == -1:
            self.filecount = self.db.filecount()

        return self.filecount

    def getDownloadCount(self):
        """ return number of downloads  """
        if self.downloadcount == -1:
            self.downloadcount = self.db.downloadcount()

        return self.downloadcount

    def getQueueCount(self, force=False):
        """number of files that have to be processed"""
        if self.queuecount == -1 or force:
            self.queuecount = self.db.queuecount()

        return self.queuecount

    def scanDownloadFolder(self):
        pass

    def searchFile(self, pattern):
        return self.db.getAllFiles(search=pattern)

    @lock
    @invalidate
    def deletePackage(self, pid):
        """delete package and all contained links"""

        p = self.getPackage(pid)
        if not p: return

        oldorder = p.packageorder
        root = p.root

        for pyfile in self.cachedFiles():
            if pyfile.packageid == pid:
                pyfile.abortDownload()

        # TODO: delete child packages
        # TODO: delete folder

        self.db.deletePackage(pid)
        self.releasePackage(pid)

        for pack in self.cachedPackages():
            if pack.root == root and pack.packageorder > oldorder:
                pack.packageorder -= 1

        self.evm.dispatchEvent("packageDeleted", pid)

    @lock
    @invalidate
    def deleteFile(self, fid):
        """deletes links"""

        f = self.getFile(fid)
        if not f: return

        pid = f.packageid
        order = f.fileorder

        if fid in self.core.threadManager.processingIds():
            f.abortDownload()

        # TODO: delete real file

        self.db.deleteFile(fid, f.fileorder, f.packageid)
        self.releaseFile(fid)

        for pyfile in self.files.itervalues():
            if pyfile.packageid == pid and pyfile.fileorder > order:
                pyfile.fileorder -= 1

        self.evm.dispatchEvent("fileDeleted", fid, pid)

    @lock
    def releaseFile(self, fid):
        """removes pyfile from cache"""
        if fid in self.files:
            del self.files[fid]

    @lock
    def releasePackage(self, pid):
        """removes package from cache"""
        if pid in self.packages:
            del self.packages[pid]

    def updateFile(self, pyfile):
        """updates file"""
        self.db.updateFile(pyfile)
        self.evm.dispatchEvent("fileUpdated", pyfile.fid, pyfile.packageid)

    def updatePackage(self, pypack):
        """updates a package"""
        self.db.updatePackage(pypack)
        self.evm.dispatchEvent("packageUpdated", pypack.pid)

    @invalidate
    def updateFileInfo(self, data, pid):
        """ updates file info (name, size, status,[ hash,] url)"""
        self.db.updateLinkInfo(data)
        self.evm.dispatchEvent("packageUpdated", pid)

    def checkAllLinksFinished(self):
        """checks if all files are finished and dispatch event"""

        if not self.getQueueCount(True):
            self.core.addonManager.dispatchEvent("allDownloadsFinished")
            self.core.log.debug("All downloads finished")
            return True

        return False

    def checkAllLinksProcessed(self, fid=-1):
        """checks if all files was processed and pyload would idle now, needs fid which will be ignored when counting"""

        # reset count so statistic will update (this is called when dl was processed)
        self.resetCount()

        if not self.db.processcount(fid):
            self.core.addonManager.dispatchEvent("allDownloadsProcessed")
            self.core.log.debug("All downloads processed")
            return True

        return False

    def checkPackageFinished(self, pyfile):
        """ checks if package is finished and calls addonmanager """

        ids = self.db.getUnfinished(pyfile.packageid)
        if not ids or (pyfile.id in ids and len(ids) == 1):
            if not pyfile.package().setFinished:
                self.core.log.info(_("Package finished: %s") % pyfile.package().name)
                self.core.addonManager.packageFinished(pyfile.package())
                pyfile.package().setFinished = True

    def resetCount(self):
        self.queuecount = -1

    @lock
    @invalidate
    def restartPackage(self, pid):
        """restart package"""
        for pyfile in self.cachedFiles():
            if pyfile.packageid == pid:
                self.restartFile(pyfile.id)

        self.db.restartPackage(pid)

        if pid in self.packages:
            self.packages[pid].setFinished = False

        self.evm.dispatchEvent("packageUpdated", pid)

    @lock
    @invalidate
    def restartFile(self, fid):
        """ restart file"""
        if fid in self.files:
            f = self.files[fid]
            f.status = DS.Queued
            f.name = f.url
            f.error = ""
            f.abortDownload()

        self.db.restartFile(fid)
        self.evm.dispatchEvent("fileUpdated", fid)


    @lock
    @invalidate
    def orderPackage(self, pid, position):

        p = self.getPackageInfo(pid)
        self.db.orderPackage(pid, p.root, p.packageorder, position)

        for pack in self.packages.itervalues():
            if pack.root != p.root or pack.packageorder < 0: continue
            if pack.pid == pid:
                pack.packageorder = position
            if p.packageorder > position:
                if position <= pack.packageorder < p.packageorder:
                    pack.packageorder += 1
            elif p.order < position:
                if position >= pack.packageorder > p.packageorder:
                    pack.packageorder -= 1

        self.db.commit()

        self.evm.dispatchEvent("packageReordered", pid, position, p.root)

    @lock
    @invalidate
    def orderFiles(self, fids, pid, position):

        files = [self.getFileInfo(fid) for fid in fids]
        orders = [f.fileorder for f in files]
        if min(orders) + len(files) != max(orders) + 1:
            raise Exception("Tried to reorder non continous block of files")

        # minimum fileorder
        f = reduce(lambda x,y: x if x.fileorder < y.fileorder else y, files)
        order = f.fileorder

        self.db.orderFiles(pid, fids, order, position)
        diff = len(fids)

        if f.fileorder > position:
            for pyfile in self.files.itervalues():
                if pyfile.packageid != f.package or pyfile.fileorder < 0: continue
                if position <= pyfile.fileorder < f.fileorder:
                    pyfile.fileorder += diff

            for i, fid in enumerate(fids):
                if fid in self.files:
                    self.files[fid].fileorder = position + i

        elif f.fileorder < position:
            for pyfile in self.files.itervalues():
                if pyfile.packageid != f.package or pyfile.fileorder < 0: continue
                if position >= pyfile.fileorder >= f.fileorder+diff:
                    pyfile.fileorder -= diff

            for i, fid in enumerate(fids):
                if fid in self.files:
                    self.files[fid].fileorder = position -diff + i + 1

        self.db.commit()

        self.evm.dispatchEvent("filesReordered", pid)

    @lock
    @invalidate
    def movePackage(self, pid, root):
        """  move pid - root """

        p = self.getPackageInfo(pid)
        dest = self.getPackageInfo(root)
        if not p: raise PackageDoesNotExists(pid)
        if not dest: raise PackageDoesNotExists(root)

        # cantor won't be happy if we put the package in itself
        if pid == root or p.root == root: return False

        # TODO move real folders

        # we assume pack is not in use anyway, so we can release it
        self.releasePackage(pid)
        self.db.movePackage(p.root, p.packageorder, pid, root)

        return True

    
    
    @lock
    @invalidate
    def moveFiles(self, fids, pid):
        """ move all fids to pid """

        f = self.getFileInfo(fids[0])
        if not f or f.package == pid:
            return False
        if not self.getPackageInfo(pid):
            raise PackageDoesNotExists(pid)

        # TODO move real files

        self.db.moveFiles(f.package, fids, pid)

        return True


    def reCheckPackage(self, pid):
        """ recheck links in package """
        data = self.db.getPackageData(pid)

        urls = []

        for pyfile in data.itervalues():
            if pyfile.status not in (DS.NA, DS.Finished, DS.Skipped):
                urls.append((pyfile.url, pyfile.pluginname))

        self.core.threadManager.createInfoThread(urls, pid)


    @invalidate
    def restartFailed(self):
        """ restart all failed links """
        # failed should not be in cache anymore, so working on db is sufficient
        self.db.restartFailed()
