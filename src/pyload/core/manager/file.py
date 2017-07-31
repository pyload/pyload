# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import time
from builtins import dict
from functools import reduce

from future import standard_library

from pyload.utils.struct.lock import RWLock, lock

from pyload.core.datatype.file import File
from pyload.core.datatype.init import DownloadStatus, TreeCollection
from pyload.core.datatype.package import (
    Package, PackageDoesNotExist, PackageStatus, RootPackage)
from pyload.core.manager.base import BaseManager

standard_library.install_aliases()


# invalidates the cache
def invalidate(func):
    def new(*args):
        args[0].downloadstats = {}
        args[0].queuestats = {}
        args[0].job_cache = {}
        return func(*args)

    return new


class FileManager(BaseManager):
    """
    Handles all request made to obtain information,
    modify status or other request for links or packages
    """
    ROOT_PACKAGE = -1
    ROOT_OWNER = -1

    def __init__(self, core):
        """
        Constructor.
        """
        BaseManager.__init__(self, core)

        # translations
        self.status_msg = [
            self._("none"),
            self._("offline"),
            self._("online"),
            self._("queued"),
            self._("paused"),
            self._("finished"),
            self._("skipped"),
            self._("failed"),
            self._("starting"),
            self._("waiting"),
            self._("downloading"),
            self._("temp. offline"),
            self._("aborted"),
            self._("not possible"),
            self._("missing"),
            self._("file mismatch"),
            self._("occupied"),
            self._("decrypting"),
            self._("processing"),
            self._("custom"),
            self._("unknown")]

        self.files = {}  # holds instances for files
        self.packages = {}  # same for packages

        self.job_cache = {}

        # locking the caches, db is already locked implicit
        self.lock = RWLock()
        # self.lock._Verbose__verbose = True

        self.downloadstats = {}  # cached dl stats
        self.queuestats = {}  # cached queue stats

        self.db = self.pyload_core.db

    def save(self):
        """
        Saves all data to backend.
        """
        self.db.commit()

    @lock(shared=True)
    def sync_save(self):
        """
        Saves all data to backend and waits until all data are written.
        """
        for file in self.files.values():
            file.sync()

        for pack in self.packages.values():
            pack.sync()

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
        self.pyload_core.evm.fire("package:updated", pid)

    @invalidate
    def add_package(self, name, folder, root, password,
                    site, comment, paused, owner):
        """
        Adds a package to database.
        """
        pid = self.db.add_package(
            name, folder, root, password, site, comment, PackageStatus.Paused
            if paused else PackageStatus.Ok, owner)
        pinfo = self.db.get_package_info(pid)

        self.pyload_core.evm.fire("package:inserted", pid,
                               pinfo.root, pinfo.packageorder)
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
            pack.timestamp = time.time()
            return pack
        else:
            info = self.db.get_package_info(pid, False)
            if not info:
                return None

            pack = Package.from_info_data(self, info)
            self.packages[pid] = pack

            return pack

    @lock(shared=True)
    def get_package_info(self, pid):
        """
        Returns dict with package information.
        """
        if pid == self.ROOT_PACKAGE:
            pinfo = RootPackage(self, self.ROOT_OWNER).to_info_data()
        elif pid in self.packages:
            pinfo = self.packages[pid].to_info_data()
            pinfo.stats = self.db.get_stats_for_package(pid)
        else:
            pinfo = self.db.get_package_info(pid)

        if not pinfo:
            return None

        # TODO: what does this todo mean?!
        # TODO: fill child packs and files
        packs = self.db.get_all_packages(root=pid)
        if pid in packs:
            del packs[pid]
        pinfo.pids = list(packs.keys())

        files = self.db.get_all_files(package=pid)
        pinfo.fids = list(files.keys())

        return pinfo

    @lock
    def get_file(self, fid):
        """
        Returns file instance.
        """
        if fid in self.files:
            return self.files[fid]
        else:
            info = self.db.get_file_info(fid)
            if not info:
                return None

            f = File.from_info_data(self, info)
            self.files[fid] = f
            return f

    @lock(shared=True)
    def get_file_info(self, fid):
        """
        Returns dict with file information.
        """
        if fid in self.files:
            return self.files[fid].to_info_data()
        return self.db.get_file_info(fid)

    def _get_tree_files(self, root, state, owner, search):
        files = self.db.get_all_files(
            package=root, state=state, search=search, owner=owner)
        # updating from cache
        for fid, file in self.files.items():
            if fid not in files:
                continue
            files[fid] = file.to_info_data()
        return files

    def _get_tree_packages(self, root, owner):
        packs = self.db.get_all_packages(root, owner=owner)
        # foreign pid, do not overwrite local pid !
        for fpid, pack in self.packages.items():
            if fpid not in packs:
                continue
            # copy the stats data
            stats = packs[fpid].stats
            packs[fpid] = pack.to_info_data()
            packs[fpid].stats = stats
        return packs

    def _reduce_tree(self, pid, packs, files):
        keep = []
        queue = [pid]
        while queue:
            fpid = queue.pop()
            keep.append(fpid)
            queue.extend(packs[fpid].pids)
        # now remove unneeded data
        for fpid in packs:
            if fpid in keep:
                continue
            del packs[fpid]
        for fid, file in files.items():
            if file.package in keep:
                continue
            del files[fid]
        return packs, files

    def _sanitize_tree(self, packs, files):
        # linear traversal over all data
        for fpid, pack in packs.items():
            if pack.fids is None:
                pack.fids = []
            if pack.pids is None:
                pack.pids = []
            root = packs.get(pack.root, None)
            if not root:
                continue
            if root.pids is None:
                root.pids = []
            root.pids.append(fpid)

        for fid, file in files.items():
            pack = packs.get(file.package, None)
            if not pack:
                continue
            pack.fids.append(fid)

        return packs, files

    @lock(shared=True)
    def get_tree(self, pid, full, state, owner=None):
        """
        Return a TreeCollection and fill the info data of containing packages.
        Optional filter only unfinished files.
        """
        view = TreeCollection(pid)

        # for depth=1, we do not need to retrieve all files/packages
        root = pid if not full else None

        packs = self._get_tree_packages(root, owner)
        files = self._get_tree_files(root, state, owner)

        # root package is not in database, create an instance
        if pid == self.ROOT_PACKAGE:
            view.root = RootPackage(self, self.ROOT_OWNER).to_info_data()
            packs[self.ROOT_PACKAGE] = view.root
        elif pid in packs:
            view.root = packs[pid]
        else:  # package does not exists
            return view

        self._sanitize_tree(packs, files)

        # cutting of tree is not good in runtime, only saves bandwidth
        # need to remove some entries
        if full and pid > -1:
            self._reduce_tree(pid, packs, files)

        # remove root
        del packs[pid]

        view.files = files
        view.packages = packs
        return view

    @lock
    def get_jobs(self, occ):
        # load jobs with file info
        if occ not in self.job_cache:
            self.job_cache[occ] = dict(
                (k, self.get_file_info(fid))
                for k, fid in self.db.get_jobs(occ).items())
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
        Number of files that have to be processed,
        failed files will not be included.
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
        pack = self.get_package(pid)
        if not pack:
            return None

        oldorder = pack.packageorder
        root = pack.root

        for file in self.cached_files():
            if file.packageid == pid:
                file.abort_download()

        self.db.delete_package(pid)
        self.release_package(pid)

        for pack in self.cached_packages():
            if pack.root == root and pack.packageorder > oldorder:
                pack.packageorder -= 1

        self.pyload_core.evm.fire("package:deleted", pid)

    @lock
    @invalidate
    def remove_file(self, fid):
        """
        Deletes links.
        """
        file = self.get_file(fid)
        if not file:
            return None

        pid = file.packageid
        order = file.fileorder

        if fid in self.pyload_core.tsm.processing_ids():
            file.abort_download()

        self.db.delete_file(fid, file.fileorder, file.packageid)
        self.release_file(fid)

        for file in self.files.values():
            if file.packageid == pid and file.fileorder > order:
                file.fileorder -= 1

        self.pyload_core.evm.fire("file:deleted", fid, pid)

    @lock
    def release_file(self, fid):
        """
        Removes file from cache.
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
    def update_file(self, file):
        """
        Updates file.
        """
        self.db.update_file(file)

        # This event is thrown with file or only fid
        self.pyload_core.evm.fire("file:updated", file)

    @invalidate
    @lock(shared=True)
    def set_download_status(self, fid, status):
        """
        Sets a download status for a file.
        """
        if fid in self.files:
            self.files[fid].set_status(status)
        else:
            self.db.set_download_status(fid, status)

        self.pyload_core.evm.fire("file:updated", fid)

    @invalidate
    def update_package(self, pack):
        """
        Updates a package.
        """
        self.db.update_package(pack)
        self.pyload_core.evm.fire("package:updated", pack.pid)

    @invalidate
    def update_file_info(self, data, pid):
        """
        Updates file info (name, size, status,[ hash,] url).
        """
        self.db.update_link_info(data)
        self.pyload_core.evm.fire("package:updated", pid)

    def check_all_links_finished(self):
        """
        Checks if all files are finished and dispatch event.
        """
        # TODO: user context?
        if not self.db.queuestats()[0]:
            self.pyload_core.adm.fire("download:allFinished")
            self.pyload_core.log.debug("All downloads finished")
            return True

        return False

    def check_all_links_processed(self, fid=-1):
        """
        Checks if all files was processed and pyload would idle now,
        needs fid which will be ignored when counting.
        """
        # reset count so statistic will update (this is called when dl was
        # processed)
        self.reset_count()

        # TODO: user context?
        if not self.db.processcount(fid):
            self.pyload_core.adm.fire("download:allProcessed")
            self.pyload_core.log.debug("All downloads processed")
            return True

        return False

    def check_package_finished(self, file):
        """
        Checks if package is finished and calls addonmanager.
        """
        ids = self.db.get_unfinished(file.packageid)
        if not ids or (file.fid in ids and len(ids) == 1):
            if not file.package().set_finished:
                self.pyload_core.log.info(
                    self._("Package finished: {0}").format(
                        file.package().name))
                self.pyload_core.adm.package_finished(file.package())
                file.package().set_finished = True

    def reset_count(self):
        self.queuecount = -1

    @lock(shared=True)
    @invalidate
    def restart_package(self, pid):
        """
        Restart package.
        """
        for file in self.cached_files():
            if file.packageid == pid:
                self.restart_file(file.fid)

        self.db.restart_package(pid)

        if pid in self.packages:
            self.packages[pid].set_finished = False

        self.pyload_core.evm.fire("package:updated", pid)

    @lock(shared=True)
    @invalidate
    def restart_file(self, fid):
        """
        Restart file.
        """
        if fid in self.files:
            file = self.files[fid]
            file.status = DownloadStatus.Queued
            file.name = file.url
            file.error = ""
            file.abort_download()

        self.db.restart_file(fid)
        self.pyload_core.evm.fire("file:updated", fid)

    @lock
    @invalidate
    def order_package(self, pid, position):
        pinfo = self.get_package_info(pid)
        self.db.order_package(pid, pinfo.root, pinfo.packageorder, position)

        for pack in self.packages.values():
            if pack.root != pinfo.root or pack.packageorder < 0:
                continue
            if pack.pid == pid:
                pack.packageorder = position
            if (pinfo.packageorder > position and
                    position <= pack.packageorder < pinfo.packageorder):
                pack.packageorder += 1
            elif (pinfo.packageorder < position and
                  position >= pack.packageorder > pinfo.packageorder):
                pack.packageorder -= 1

        self.db.commit()

        self.pyload_core.evm.fire("package:reordered", pid, position, pinfo.root)

    def _get_first_fileinfo(self, files):
        # NOTE: Equality between fileorders should never happen...
        return reduce(
            lambda x, y: x if x.fileorder <= y.fileorder else y, files)

    def _order_files(self, fids, finfo, position):
        diff = len(fids)
        incr = 0
        files = (file for file in self.files.values() if not (
            file.fileorder < 0 or file.packageid != finfo.package))
        if finfo.fileorder > position:
            for file in files:
                if not (position <= file.fileorder < finfo.fileorder):
                    continue
                file.fileorder += diff
            diff = 0
        elif finfo.fileorder < position:
            for file in files:
                if not (position >= file.fileorder >= finfo.fileorder + diff):
                    continue
                file.fileorder -= diff
            incr = 1
        for i, fid in enumerate(fids):
            if fid not in self.files:
                continue
            self.files[fid].fileorder = position - diff + i + incr

    @lock
    @invalidate
    def order_files(self, fids, pid, position):
        files = [self.get_file_info(fid) for fid in fids]
        orders = (finfo.fileorder for finfo in files)
        if min(orders) + len(files) != max(orders) + 1:
            raise Exception("Tried to reorder non continuous block of files")

        finfo = self._get_first_fileinfo(files)

        order = finfo.fileorder  # minimum fileorder
        self.db.order_files(pid, fids, order, position)

        self._order_files(fids, finfo, position)

        self.db.commit()
        self.pyload_core.evm.fire("file:reordered", pid)

    @lock(shared=True)
    @invalidate
    def move_package(self, pid, root):
        """
        Move pid - root.
        """
        pinfo = self.get_package_info(pid)
        dest = self.get_package_info(root)
        if not pinfo:
            raise PackageDoesNotExist(pid)
        if not dest:
            raise PackageDoesNotExist(root)

        # cantor won't be happy if we put the package in itself
        if pid == root or pinfo.root == root:
            return False

        # we assume pack is not in use anyway, so we can release it
        self.release_package(pid)
        self.db.move_package(pinfo.root, pinfo.packageorder, pid, root)

        return True

    @lock(shared=True)
    @invalidate
    def move_files(self, fids, pid):
        """
        Move all fids to pid.
        """
        finfo = self.get_file_info(fids[0])
        if not finfo or finfo.package == pid:
            return False
        if not self.get_package_info(pid):
            raise PackageDoesNotExist(pid)

        self.db.move_files(finfo.package, fids, pid)

        return True

    @invalidate
    def re_check_package(self, pid):
        """
        Recheck links in package.
        """
        data = self.db.get_package_data(pid)

        urls = []

        for file in data.values():
            if file.status not in (
                    DownloadStatus.NA, DownloadStatus.Finished,
                    DownloadStatus.Skipped):
                urls.append((file.url, file.pluginname))

        if not urls:
            return None

        self.pyload_core.iom.create_info_thread(urls, pid)

    @invalidate
    def restart_failed(self):
        """
        Restart all failed links.
        """
        # failed should not be in cache anymore, so working on db is sufficient
        self.db.restart_failed()
