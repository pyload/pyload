# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from builtins import dict, object
from functools import reduce
from time import time

from future import standard_library
standard_library.install_aliases()

from pyload.utils.decorator import lock, readlock
from pyload.utils.struct.lock import ReadWriteLock

from ..datatype.file import PyFile
from ..datatype.init import DownloadStatus, TreeCollection
from ..datatype.package import (PackageDoesNotExist, PackageStatus, PyPackage,
                                RootPackage)


# invalidates the cache
def invalidate(func):
    def new(*args):
        args[0].downloadstats = {}
        args[0].queuestats = {}
        args[0].job_cache = {}
        return func(*args)

    return new


class FileManager(object):
    """
    Handles all request made to obtain information,
    modify status or other request for links or packages
    """
    __slots__ = [
        'db',
        'downloadstats',
        'files',
        'job_cache',
        'lock',
        'packages',
        'pyload',
        'queuecount',
        'queuestats',
        'status_msg']

    ROOT_PACKAGE = -1
    ROOT_OWNER = -1

    def __init__(self, core):
        """
        Constructor.
        """
        self.pyload = core

        # translations
        self.status_msg = [_("none"), _("offline"), _("online"), _("queued"), _("paused"),
                           _("finished"), _("skipped"), _(
                               "failed"), _("starting"), _("waiting"),
                           _("downloading"), _("temp. offline"), _(
                               "aborted"), _("not possible"), _("missing"),
                           _("file mismatch"), _("occupied"), _(
                               "decrypting"), _("processing"), _("custom"),
                           _("unknown")]

        self.files = {}  #: holds instances for files
        self.packages = {}  #: same for packages

        self.job_cache = {}

        # locking the caches, db is already locked implicit
        self.lock = ReadWriteLock()
        #self.lock._Verbose__verbose = True

        self.downloadstats = {}  #: cached dl stats
        self.queuestats = {}  #: cached queue stats

        self.db = self.pyload.db

    def save(self):
        """
        Saves all data to backend.
        """
        self.db.commit()

    @readlock
    def sync_save(self):
        """
        Saves all data to backend and waits until all data are written.
        """
        for pyfile in self.files.values():
            pyfile.sync()

        for pypack in self.packages.values():
            pypack.sync()

        self.db.sync_save()

    def cached_files(self):
        return list(self.files.values())

    def cached_packages(self):
        return list(self.packages.values())

    def get_collector(self):
        raise NotImplementedError

    @invalidate
    def add_links(self, data, pid, owner):
        """
        Add links, data = (url, plugin) tuple. Internal method should use API.
        """
        self.db.add_links(data, pid, owner)
        self.pyload.evm.fire("package:updated", pid)

    @invalidate
    def add_package(self, name, folder, root, password,
                    site, comment, paused, owner):
        """
        Adds a package to database.
        """
        pid = self.db.add_package(name, folder, root, password, site, comment,
                                  PackageStatus.Paused if paused else PackageStatus.Ok, owner)
        p = self.db.get_package_info(pid)

        self.pyload.evm.fire("package:inserted", pid, p.root, p.packageorder)
        return pid

    @lock
    def get_package(self, pid):
        """
        Return package instance.
        """
        if pid == self.ROOT_PACKAGE:
            return RootPackage(self, self.ROOT_OWNER)
        elif pid in self.packages:
            pack = self.packages[pid]
            pack.timestamp = time()
            return pack
        else:
            info = self.db.get_package_info(pid, False)
            if not info:
                return None

            pack = PyPackage.from_info_data(self, info)
            self.packages[pid] = pack

            return pack

    @readlock
    def get_package_info(self, pid):
        """
        Returns dict with package information.
        """
        if pid == self.ROOT_PACKAGE:
            pack = RootPackage(self, self.ROOT_OWNER).to_info_data()
        elif pid in self.packages:
            pack = self.packages[pid].to_info_data()
            pack.stats = self.db.get_stats_for_package(pid)
        else:
            pack = self.db.get_package_info(pid)

        if not pack:
            return None

        # TODO: what does this todo mean?!
        # TODO: fill child packs and files
        packs = self.db.get_all_packages(root=pid)
        if pid in packs:
            del packs[pid]
        pack.pids = list(packs.keys())

        files = self.db.get_all_files(package=pid)
        pack.fids = list(files.keys())

        return pack

    @lock
    def get_file(self, fid):
        """
        Returns pyfile instance.
        """
        if fid in self.files:
            return self.files[fid]
        else:
            info = self.db.get_file_info(fid)
            if not info:
                return None

            f = PyFile.from_info_data(self, info)
            self.files[fid] = f
            return f

    @readlock
    def get_file_info(self, fid):
        """
        Returns dict with file information.
        """
        if fid in self.files:
            return self.files[fid].to_info_data()

        return self.db.get_file_info(fid)

    @readlock
    def get_tree(self, pid, full, state, owner=None, search=None):
        """
        Return a TreeCollection and fill the info data of containing packages.
        Optional filter only unfinished files.
        """
        view = TreeCollection(pid)

        # for depth=1, we do not need to retrieve all files/packages
        root = pid if not full else None

        packs = self.db.get_all_packages(root, owner=owner)
        files = self.db.get_all_files(
            package=root, state=state, search=search, owner=owner)

        # updating from cache
        for fid, f in self.files.items():
            if fid in files:
                files[fid] = f.to_info_data()

        # foreign pid, do not overwrite local pid !
        for fpid, p in self.packages.items():
            if fpid in packs:
                # copy the stats data
                stats = packs[fpid].stats
                packs[fpid] = p.to_info_data()
                packs[fpid].stats = stats

        # root package is not in database, create an instance
        if pid == self.ROOT_PACKAGE:
            view.root = RootPackage(self, self.ROOT_OWNER).to_info_data()
            packs[self.ROOT_PACKAGE] = view.root
        elif pid in packs:
            view.root = packs[pid]
        else:  #: package does not exists
            return view

        # linear traversal over all data
        for fpid, p in packs.items():
            if p.fids is None:
                p.fids = []
            if p.pids is None:
                p.pids = []

            root = packs.get(p.root, None)
            if root:
                if root.pids is None:
                    root.pids = []
                root.pids.append(fpid)

        for fid, f in files.items():
            p = packs.get(f.package, None)
            if p:
                p.fids.append(fid)

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

        # remove root
        del packs[pid]
        view.files = files
        view.packages = packs

        return view

    @lock
    def get_jobs(self, occ):

        # load jobs with file info
        if occ not in self.job_cache:
            self.job_cache[occ] = dict((k, self.get_file_info(fid)) for k, fid
                                       in self.db.get_jobs(occ).items())

        return self.job_cache[occ]

    def get_download_stats(self, user=None):
        """
        Return number of downloads.
        """
        if user not in self.downloadstats:
            self.downloadstats[user] = self.db.downloadstats(user)

        return self.downloadstats[user]

    def get_queue_stats(self, user=None, force=False):
        """
        Number of files that have to be processed, failed files will not be included.
        """
        if user not in self.queuestats or force:
            self.queuestats[user] = self.db.queuestats(user)

        return self.queuestats[user]

    def scan_download_folder(self):
        raise NotImplementedError

    @lock
    @invalidate
    def remove_package(self, pid):
        """
        Delete package and all contained links.
        """
        p = self.get_package(pid)
        if not p:
            return None

        oldorder = p.packageorder
        root = p.root

        for pyfile in self.cached_files():
            if pyfile.packageid == pid:
                pyfile.abort_download()

        self.db.delete_package(pid)
        self.release_package(pid)

        for pack in self.cached_packages():
            if pack.root == root and pack.packageorder > oldorder:
                pack.packageorder -= 1

        self.pyload.evm.fire("package:deleted", pid)

    @lock
    @invalidate
    def remove_file(self, fid):
        """
        Deletes links.
        """
        f = self.get_file(fid)
        if not f:
            return None

        pid = f.packageid
        order = f.fileorder

        if fid in self.pyload.dlm.processing_ids():
            f.abort_download()

        self.db.delete_file(fid, f.fileorder, f.packageid)
        self.release_file(fid)

        for pyfile in self.files.values():
            if pyfile.packageid == pid and pyfile.fileorder > order:
                pyfile.fileorder -= 1

        self.pyload.evm.fire("file:deleted", fid, pid)

    @lock
    def release_file(self, fid):
        """
        Removes pyfile from cache.
        """
        if fid in self.files:
            del self.files[fid]

    @lock
    def release_package(self, pid):
        """
        Removes package from cache.
        """
        if pid in self.packages:
            del self.packages[pid]

    @invalidate
    def update_file(self, pyfile):
        """
        Updates file.
        """
        self.db.update_file(pyfile)

        # This event is thrown with pyfile or only fid
        self.pyload.evm.fire("file:updated", pyfile)

    @invalidate
    @readlock
    def set_download_status(self, fid, status):
        """
        Sets a download status for a file.
        """
        if fid in self.files:
            self.files[fid].set_status(status)
        else:
            self.db.set_download_status(fid, status)

        self.pyload.evm.fire("file:updated", fid)

    @invalidate
    def update_package(self, pypack):
        """
        Updates a package.
        """
        self.db.update_package(pypack)
        self.pyload.evm.fire("package:updated", pypack.pid)

    @invalidate
    def update_file_info(self, data, pid):
        """
        Updates file info (name, size, status,[ hash,] url).
        """
        self.db.update_link_info(data)
        self.pyload.evm.fire("package:updated", pid)

    def check_all_links_finished(self):
        """
        Checks if all files are finished and dispatch event.
        """

        # TODO: user context?
        if not self.db.queuestats()[0]:
            self.pyload.adm.fire("download:allFinished")
            self.pyload.log.debug("All downloads finished")
            return True

        return False

    def check_all_links_processed(self, fid=-1):
        """
        Checks if all files was processed and pyload would idle now, needs fid which will be ignored when counting.
        """

        # reset count so statistic will update (this is called when dl was
        # processed)
        self.reset_count()

        # TODO: user context?
        if not self.db.processcount(fid):
            self.pyload.adm.fire("download:allProcessed")
            self.pyload.log.debug("All downloads processed")
            return True

        return False

    def check_package_finished(self, pyfile):
        """
        Checks if package is finished and calls addonmanager.
        """
        ids = self.db.get_unfinished(pyfile.packageid)
        if not ids or (pyfile.fid in ids and len(ids) == 1):
            if not pyfile.package().set_finished:
                self.pyload.log.info(
                    _("Package finished: {0}").format(pyfile.package().name))
                self.pyload.adm.package_finished(pyfile.package())
                pyfile.package().set_finished = True

    def reset_count(self):
        self.queuecount = -1

    @readlock
    @invalidate
    def restart_package(self, pid):
        """
        Restart package.
        """
        for pyfile in self.cached_files():
            if pyfile.packageid == pid:
                self.restart_file(pyfile.fid)

        self.db.restart_package(pid)

        if pid in self.packages:
            self.packages[pid].set_finished = False

        self.pyload.evm.fire("package:updated", pid)

    @readlock
    @invalidate
    def restart_file(self, fid):
        """
        Restart file.
        """
        if fid in self.files:
            f = self.files[fid]
            f.status = DownloadStatus.Queued
            f.name = f.url
            f.error = ""
            f.abort_download()

        self.db.restart_file(fid)
        self.pyload.evm.fire("file:updated", fid)

    @lock
    @invalidate
    def order_package(self, pid, position):

        p = self.get_package_info(pid)
        self.db.order_package(pid, p.root, p.packageorder, position)

        for pack in self.packages.values():
            if pack.root != p.root or pack.packageorder < 0:
                continue
            if pack.pid == pid:
                pack.packageorder = position
            if p.packageorder > position:
                if position <= pack.packageorder < p.packageorder:
                    pack.packageorder += 1
            elif p.order < position:
                if position >= pack.packageorder > p.packageorder:
                    pack.packageorder -= 1

        self.db.commit()

        self.pyload.evm.fire("package:reordered", pid, position, p.root)

    @lock
    @invalidate
    def order_files(self, fids, pid, position):

        files = [self.get_file_info(fid) for fid in fids]
        orders = [f.fileorder for f in files]
        if min(orders) + len(files) != max(orders) + 1:
            raise Exception("Tried to reorder non continuous block of files")

        # minimum fileorder
        f = reduce(lambda x, y: x if x.fileorder < y.fileorder else y, files)
        order = f.fileorder

        self.db.order_files(pid, fids, order, position)
        diff = len(fids)

        if f.fileorder > position:
            for pyfile in self.files.values():
                if pyfile.packageid != f.package or pyfile.fileorder < 0:
                    continue
                if position <= pyfile.fileorder < f.fileorder:
                    pyfile.fileorder += diff

            for i, fid in enumerate(fids):
                if fid in self.files:
                    self.files[fid].fileorder = position + i

        elif f.fileorder < position:
            for pyfile in self.files.values():
                if pyfile.packageid != f.package or pyfile.fileorder < 0:
                    continue
                if position >= pyfile.fileorder >= f.fileorder + diff:
                    pyfile.fileorder -= diff

            for i, fid in enumerate(fids):
                if fid in self.files:
                    self.files[fid].fileorder = position - diff + i + 1

        self.db.commit()

        self.pyload.evm.fire("file:reordered", pid)

    @readlock
    @invalidate
    def move_package(self, pid, root):
        """
        Move pid - root.
        """
        p = self.get_package_info(pid)
        dest = self.get_package_info(root)
        if not p:
            raise PackageDoesNotExist(pid)
        if not dest:
            raise PackageDoesNotExist(root)

        # cantor won't be happy if we put the package in itself
        if pid == root or p.root == root:
            return False

        # we assume pack is not in use anyway, so we can release it
        self.release_package(pid)
        self.db.move_package(p.root, p.packageorder, pid, root)

        return True

    @readlock
    @invalidate
    def move_files(self, fids, pid):
        """
        Move all fids to pid.
        """
        f = self.get_file_info(fids[0])
        if not f or f.package == pid:
            return False
        if not self.get_package_info(pid):
            raise PackageDoesNotExist(pid)

        self.db.move_files(f.package, fids, pid)

        return True

    @invalidate
    def re_check_package(self, pid):
        """
        Recheck links in package.
        """
        data = self.db.get_package_data(pid)

        urls = []

        for pyfile in data.values():
            if pyfile.status not in (
                    DownloadStatus.NA, DownloadStatus.Finished, DownloadStatus.Skipped):
                urls.append((pyfile.url, pyfile.pluginname))

        self.pyload.thm.create_info_thread(urls, pid)

    @invalidate
    def restart_failed(self):
        """
        Restart all failed links.
        """

        # failed should not be in cache anymore, so working on db is sufficient
        self.db.restart_failed()
