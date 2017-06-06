# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from builtins import int

from future import standard_library

from pyload.utils.layer.legacy.collections_ import OrderedDict

from ..api.init import statestring
from ..datatype.file import FileInfo, guess_type
from ..datatype.init import DownloadInfo, DownloadState
from ..datatype.package import PackageInfo, PackageStats
from .backend import DatabaseMethods, async, inner, queue

standard_library.install_aliases()


_zero_stats = PackageStats(0, 0, 0, 0)


class FileMethods(DatabaseMethods):

    @queue
    def filecount(self):
        """
        Returns number of files, currently only used for debugging.
        """
        self.c.execute("SELECT COUNT(*) FROM files")
        return self.c.fetchone()[0]

    @queue
    def downloadstats(self, user=None):
        """
        Number of downloads and size.
        """
        if user is None:
            self.c.execute("SELECT COUNT(*), SUM(f.size) FROM files f "
                           "WHERE dlstatus != 0")
        else:
            self.c.execute(
                "SELECT COUNT(*), SUM(f.size) FROM files f WHERE f.owner=? "
                "AND dlstatus != 0", (user,))

        r = self.c.fetchone()
        # sum is None when no elements are added
        return (r[0], r[1] if r[1] is not None else 0) if r else (0, 0)

    # TODO: missing and not possible DLs ?
    @queue
    def queuestats(self, user=None):
        """
        Number and size of files in queue not finished yet.
        """
        # status not in NA, finished, skipped
        if user is None:
            self.c.execute(
                "SELECT COUNT(*), SUM(f.size) FROM files f WHERE dlstatus "
                "NOT IN (0,5,6)")
        else:
            self.c.execute(
                "SELECT COUNT(*), SUM(f.size) FROM files f WHERE f.owner=? "
                "AND dlstatus NOT IN (0,5,6)", (user,))

        r = self.c.fetchone()
        return (r[0], r[1] if r[1] is not None else 0) if r else (0, 0)

    # TODO: multi user?
    @queue
    def processcount(self, fid=-1, user=None):
        """
        Number of files which have to be processed.
        """
        # status in online, queued, starting, waiting, downloading
        self.c.execute(
            "SELECT COUNT(*), SUM(size) FROM files "
            "WHERE dlstatus IN (2,3,8,9,10) AND fid != ?", (fid,))
        return self.c.fetchone()[0]

    @queue
    def processstats(self, user=None):
        if user is None:
            self.c.execute("SELECT COUNT(*), SUM(size) FROM files "
                           "WHERE dlstatus IN (2,3,8,9,10)")
        else:
            self.c.execute(
                "SELECT COUNT(*), SUM(f.size) FROM files f "
                "WHERE f.owner=? AND dlstatus IN (2,3,8,9,10)", (user,))
        r = self.c.fetchone()
        return (r[0], r[1] if r[1] is not None else 0) if r else (0, 0)

    @queue
    def add_link(self, url, name, plugin, package, owner):
        # mark file status initially as missing, dlstatus - queued
        self.c.execute(
            'INSERT INTO files(url, name, plugin, status, dlstatus, package, '
            'owner) VALUES(?,?,?,1,3,?,?)',
            (url, name, plugin, package, owner))
        return self.c.lastrowid

    @async
    def add_links(self, links, package, owner):
        """
        Links is a list of tuples (url, plugin).
        """
        links = [(x[0], x[0], x[1], package, owner) for x in links]
        self.c.executemany(
            'INSERT INTO files(url, name, plugin, status, dlstatus, package, '
            'owner) VALUES(?,?,?,1,3,?,?)', links)

    @queue
    def add_file(self, name, size, media, package, owner):
        # file status - ok, dl status NA
        self.c.execute(
            'INSERT INTO files(name, size, media, package, owner) '
            'VALUES(?,?,?,?,?)', (name, size, media, package, owner))
        return self.c.lastrowid

    @queue
    def add_package(self, name, folder, root, password,
                    site, comment, status, owner):
        self.c.execute(
            'INSERT INTO packages(name, folder, root, password, site, '
            'comment, status, owner) VALUES(?,?,?,?,?,?,?,?)',
            (name, folder, root, password, site, comment, status, owner))
        return self.c.lastrowid

    @async
    def delete_package(self, pid, owner=None):
        # order updated by trigger, as well as links deleted
        if owner is None:
            self.c.execute('DELETE FROM packages WHERE pid=?', (pid,))
        else:
            self.c.execute(
                'DELETE FROM packages WHERE pid=? AND owner=?', (pid, owner))

    @async
    def delete_file(self, fid, order, package, owner=None):
        """
        To delete a file order and package of it is needed.
        """
        if owner is None:
            self.c.execute('DELETE FROM files WHERE fid=?', (fid,))
            self.c.execute(
                'UPDATE files SET fileorder=fileorder-1 WHERE fileorder > ? '
                'AND package=?', (order, package))
        else:
            self.c.execute(
                'DELETE FROM files WHERE fid=? AND owner=?', (fid, owner))
            self.c.execute(
                'UPDATE files SET fileorder=fileorder-1 WHERE fileorder > ? '
                'AND package=? AND owner=?', (order, package, owner))

    @queue
    def get_all_files(self, package=None, search=None, state=None, owner=None):
        """
        Return dict with file information

        :param package: optional package to filter out
        :param search: or search string for file name
        :param unfinished: filter by dlstatus not finished
        :param owner: only specific owner
        """
        qry = ('SELECT fid, name, owner, size, status, media, added, '
               'fileorder, url, plugin, hash, dlstatus, error, package '
               'FROM files WHERE ')

        arg = []

        if state is not None and state != DownloadState.All:
            qry += "dlstatus IN ({0}) AND ".format(statestring(state))
        if owner is not None:
            qry += 'owner=? AND '
            arg.append(owner)

        if package is not None:
            arg.append(package)
            qry += 'package=? AND '
        if search is not None:
            search = "%%{0}%%".format(search.strip("%"))
            arg.append(search)
            qry += "name LIKE ? "

        # make qry valid
        if qry.endswith("WHERE "):
            qry = qry[:-6]
        if qry.endswith("AND "):
            qry = qry[:-4]

        self.c.execute(qry + "ORDER BY package, fileorder", arg)

        data = OrderedDict()
        for r in self.c.fetchall():
            finfo = FileInfo(r[0], r[1], r[13], r[2],
                             r[3], r[4], r[5], r[6], r[7])
            if r[11] > 0:  # dl status != NA
                finfo.download = DownloadInfo(
                    r[8],
                    r[9],
                    r[10],
                    r[11],
                    self.__manager.status_msg[r[11]],
                    r[12])
            data[r[0]] = finfo

        return data

    @queue
    def get_matching_filenames(self, pattern, owner=None):
        """
        Return matching file names for pattern, useful for search suggestions.
        """
        qry = 'SELECT name FROM files WHERE name LIKE ?'
        args = ["%%{0}%%".format(pattern.strip("%"))]
        if owner:
            qry += " AND owner=?"
            args.append(owner)

        self.c.execute(qry, args)
        return [r[0] for r in self.c.fetchall()]

    @queue
    def get_all_packages(self, root=None, owner=None, tags=None):
        """
        Return dict with package information

        :param root: optional root to filter
        :param owner: optional user id
        :param tags: optional tag list
        """
        qry = (
            'SELECT pid, name, folder, root, owner, site, comment, password, '
            'added, tags, status, shared, packageorder FROM packages{} '
            'ORDER BY root, packageorder')

        if root is None:
            stats = self.get_package_stats(owner=owner)
            if owner is None:
                self.c.execute(qry.format(""))
            else:
                self.c.execute(qry.format(" WHERE owner=?"), (owner,))
        else:
            stats = self.get_package_stats(root=root, owner=owner)
            if owner is None:
                self.c.execute(qry.format(
                    ' WHERE root=? OR pid=?'), (root, root))
            else:
                self.c.execute(
                    qry.format(' WHERE (root=? OR pid=?) AND owner=?'),
                    (root, root, owner))

        data = OrderedDict()
        for r in self.c.fetchall():
            data[r[0]] = PackageInfo(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[
                    8], r[9].split(","), r[10], r[11], r[12],
                stats.get(r[0], _zero_stats)
            )
        return data

    @inner
    def get_package_stats(self, pid=None, root=None, owner=None):
        qry = (
            "SELECT p.pid, SUM(f.size) AS sizetotal, COUNT(f.fid) "
            "AS linkstotal, sizedone, linksdone FROM packages p JOIN files f "
            "ON p.pid = f.package AND f.dlstatus > 0 {0} LEFT OUTER "
            "JOIN (SELECT p.pid AS pid, SUM(f.size) AS sizedone, COUNT(f.fid) "
            "AS linksdone FROM packages p JOIN files f "
            "ON p.pid = f.package {0} AND f.dlstatus in (5,6) "
            "GROUP BY p.pid) s ON s.pid = p.pid GROUP BY p.pid")

        # status in (finished, skipped, processing)

        if root is not None:
            self.c.execute(qry.format(
                "AND (p.root=:root OR p.pid=:root)"), locals())
        elif pid is not None:
            self.c.execute(qry.format("AND p.pid=:pid"), locals())
        elif owner is not None:
            self.c.execute(qry.format("AND p.owner=:owner"), locals())
        else:
            self.c.execute(qry.format(""))

        data = {}
        for r in self.c.fetchall():
            data[r[0]] = PackageStats(
                r[2] if r[2] else 0,
                r[4] if r[4] else 0,
                int(r[1]) if r[1] else 0,
                int(r[3]) if r[3] else 0,
            )

        return data

    @queue
    def get_stats_for_package(self, pid):
        return self.get_package_stats(pid=pid)[pid]

    @queue
    def get_file_info(self, fid, force=False):
        """
        Get data for specific file, when force is true download info
        will be appended.
        """
        self.c.execute(
            'SELECT fid, name, owner, size, status, media, added, fileorder, '
            'url, plugin, hash, dlstatus, error, package FROM files '
            'WHERE fid=?', (fid,))
        r = self.c.fetchone()
        if not r:
            return None
        finfo = FileInfo(r[0], r[1], r[13], r[2], r[3], r[4], r[5], r[6], r[7])
        if r[11] > 0 or force:
            finfo.download = DownloadInfo(
                r[8],
                r[9],
                r[10],
                r[11],
                self.__manager.status_msg[r[11]],
                r[12])
        return finfo

    @queue
    def get_package_info(self, pid, stats=True):
        """
        Get data for a specific package, optionally with package stats.
        """
        if stats:
            stats = self.get_package_stats(pid=pid)

        self.c.execute(
            'SELECT pid, name, folder, root, owner, site, comment, password, '
            'added, tags, status, shared, packageorder FROM packages '
            'WHERE pid=?', (pid,))

        r = self.c.fetchone()
        if not r:
            return None
        else:
            return PackageInfo(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[
                    8], r[9].split(","), r[10], r[11], r[12],
                stats.get(r[0], _zero_stats) if stats else None
            )

    # TODO: does this need owner?
    @async
    def update_link_info(self, data):
        """
        Data is list of tuples (name, size, status,[ hash,] url).
        """
        # inserts media type as n-1th arguments
        data = [info[:-1] + (guess_type(info[0]), info[-1]) for info in data]

        # status in (NA, Offline, Online, Queued, TempOffline)
        if data and len(data[0]) == 5:
            self.c.executemany(
                'UPDATE files SET name=?, size=?, dlstatus=?, media=? '
                'WHERE url=? AND dlstatus IN (0,1,2,3,11)', data)
        else:
            self.c.executemany(
                'UPDATE files SET name=?, size=?, dlstatus=?, hash=?, media=? '
                'WHERE url=? AND dlstatus IN (0,1,2,3,11)', data)

    @async
    def update_file(self, f):
        self.c.execute(
            'UPDATE files SET name=?, size=?, status=?,'
            'media=?, url=?, hash=?, dlstatus=?, error=? WHERE fid=?',
            (f.name, f.size, f.filestatus, f.media, f.url, f.hash,
             f.status, f.error, f.fid))

    @async
    def set_download_status(self, fid, status):
        self.c.execute(
            'UPDATE files SET dlstatus=? WHERE fid=?', (status, fid))

    @async
    def update_package(self, p):
        self.c.execute(
            'UPDATE packages SET name=?, folder=?, site=?, comment=?, '
            'password=?, tags=?, status=?, shared=? WHERE pid=?',
            (p.name, p.folder, p.site, p.comment, p.password,
             ",".join(p.tags), p.status, p.shared, p.pid))

    # TODO: most modifying methods needs owner argument to avoid checking
    # beforehand
    @async
    def order_package(self, pid, root, oldorder, order):
        if oldorder > order:  # package moved upwards
            self.c.execute(
                'UPDATE packages SET packageorder=packageorder+1 '
                'WHERE packageorder >= ? AND packageorder < ? AND root=? '
                'AND packageorder >= 0', (order, oldorder, root))
        elif oldorder < order:  # moved downwards
            self.c.execute(
                'UPDATE packages SET packageorder=packageorder-1 '
                'WHERE packageorder <= ? AND packageorder > ? AND root=? '
                'AND packageorder >= 0', (order, oldorder, root))

        self.c.execute(
            'UPDATE packages SET packageorder=? WHERE pid=?', (order, pid))

    @async
    def order_files(self, pid, fids, oldorder, order):
        diff = len(fids)
        data = []

        if oldorder > order:  # moved upwards
            self.c.execute(
                'UPDATE files SET fileorder=fileorder+? WHERE fileorder >= ? '
                'AND fileorder < ? AND package=?',
                (diff, order, oldorder, pid))
            data = [(order + i, fid) for i, fid in enumerate(fids)]
        elif oldorder < order:
            self.c.execute(
                'UPDATE files SET fileorder=fileorder-? WHERE fileorder <= ? '
                'AND fileorder >= ? AND package=?',
                (diff, order, oldorder + diff, pid))
            data = [(order - diff + i + 1, fid) for i, fid in enumerate(fids)]

        self.c.executemany('UPDATE files SET fileorder=? WHERE fid=?', data)

    @async
    def move_files(self, pid, fids, package):
        self.c.execute(
            'SELECT max(fileorder) FROM files WHERE package=?', (package,))
        r = self.c.fetchone()
        order = (r[0] if r[0] else 0) + 1

        self.c.execute(
            'UPDATE files SET fileorder=fileorder-? WHERE fileorder > ? '
            'AND package=?', (len(fids), order, pid))

        data = [(package, order + i, fid) for i, fid in enumerate(fids)]
        self.c.executemany(
            'UPDATE files SET package=?, fileorder=? WHERE fid=?', data)

    @async
    def move_package(self, root, order, pid, dpid):
        self.c.execute(
            'SELECT max(packageorder) FROM packages WHERE root=?', (dpid,))
        r = self.c.fetchone()
        max = (r[0] if r[0] else 0) + 1

        self.c.execute(
            'UPDATE packages SET packageorder=packageorder-1 '
            'WHERE packageorder > ? AND root=?', (order, root))

        self.c.execute(
            'UPDATE packages SET root=?, packageorder=? WHERE pid=?',
            (dpid, max, pid))

    @async
    def restart_file(self, fid):
        # status -> queued
        self.c.execute(
            'UPDATE files SET dlstatus=3, error="" WHERE fid=?', (fid,))

    @async
    def restart_package(self, pid):
        # status -> queued
        self.c.execute('UPDATE files SET status=3 WHERE package=?', (pid,))

    @queue
    def get_jobs(self, occ):
        """
        Return file ids, which are suitable for download and
        do not use a occupied plugin.
        """
        cmd = "({0})".format(", ".join("'{0}'".format(x) for x in occ))

        # dlstatus in online, queued, occupied | package status = ok
        cmd = (
            "SELECT f.owner, f.fid FROM files as f INNER JOIN packages "
            "as p ON f.package=p.pid WHERE f.owner=? AND f.plugin NOT IN {} "
            "AND f.dlstatus IN (2,3,16) AND p.status=0 "
            "ORDER BY p.packageorder ASC, f.fileorder ASC LIMIT 1").format(cmd)

        self.c.execute("SELECT uid FROM users")
        uids = self.c.fetchall()
        jobs = {}
        # get jobs for all uids
        for uid in uids:
            self.c.execute(cmd, uid)
            r = self.c.fetchone()
            if r:
                jobs[r[0]] = r[1]

        return jobs

    @queue
    def get_unfinished(self, pid):
        """
        Return list of max length 3 ids with pyfiles in package not finished
        or processed.
        """
        # status in finished, skipped, processing
        self.c.execute(
            "SELECT fid FROM files WHERE package=? AND dlstatus "
            "NOT IN (5, 6, 14) LIMIT 3", (pid,))
        return [r[0] for r in self.c.fetchall()]

    @queue
    def restart_failed(self, owner=None):
        # status=queued, where status in failed, aborted, temp offline, file
        # mismatch
        self.c.execute(
            "UPDATE files SET dlstatus=3, error='' WHERE dlstatus "
            "IN (7, 11, 12, 15)")

    @queue
    def find_duplicates(self, id, folder, filename):
        """
        Checks if filename exists with different id and same package,
        dlstatus = finished.
        """
        # TODO: also check root of package
        self.c.execute(
            "SELECT f.plugin FROM files f INNER JOIN packages as p "
            "ON f.package=p.pid AND p.folder=? WHERE f.fid!=? "
            "AND f.dlstatus=5 AND f.name=?", (folder, id, filename))
        return self.c.fetchone()

    @queue
    def purge_links(self):
        # fstatus = missing
        self.c.execute("DELETE FROM files WHERE status == 1")

    @queue
    def purge_all(self):  # only used for debugging
        self.c.execute("DELETE FROM packages")
        self.c.execute("DELETE FROM files")
        self.c.execute("DELETE FROM collector")


FileMethods.register()
