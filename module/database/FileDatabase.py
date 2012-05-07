#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""
from new_collections import OrderedDict

from module.Api import DownloadInfo, LinkStatus, FileInfo, PackageInfo, PackageStats
from module.database import DatabaseMethods, queue, async, inner

default = PackageStats(0, 0, 0, 0)

class FileMethods(DatabaseMethods):
    @queue
    def filecount(self):
        """returns number of files"""
        self.c.execute("SELECT COUNT(*) FROM files")
        return self.c.fetchone()[0]

    @queue
    def queuecount(self):
        """ number of files in queue not finished yet"""
        # status not in NA, finished, skipped
        self.c.execute("SELECT COUNT(*) FROM files WHERE dlstatus NOT IN (0,5,6)")
        return self.c.fetchone()[0]

    @queue
    def processcount(self, fid):
        """ number of files which have to be processed """
        # status in online, queued, starting, waiting, downloading
        self.c.execute("SELECT COUNT(*) FROM files as WHERE dlstatus IN (2,3,8,9,10) AND fid != ?", (str(fid), ))
        return self.c.fetchone()[0]

    @queue
    def addLink(self, url, name, plugin, package):
        # mark file status initially as missing, dlstatus - queued
        self.c.execute('INSERT INTO files(url, name, plugin, status, dlstatus, package) VALUES(?,?,?,1,3,?)',
            (url, name, plugin, package))
        return self.c.lastrowid

    @async
    def addLinks(self, links, package):
        """ links is a list of tuples (url, plugin)"""
        links = [(x[0], x[0], x[1], package) for x in links]
        self.c.executemany('INSERT INTO files(url, name, plugin, status, dlstatus, package) VALUES(?,?,?,1,3,?)', links)

    @queue
    def addFile(self, name, size, media, package):
        # file status - ok, dl status NA
        self.c.execute('INSERT INTO files(name, size, media, package) VALUES(?,?,?,?)',
            (name, size, media, package))
        return self.c.lastrowid

    @queue
    def addPackage(self, name, folder, root, password, site, comment, status):
        self.c.execute('INSERT INTO packages(name, folder, root, password, site, comment, status) VALUES(?,?,?,?,?,?,?)'
            ,
            (name, folder, root, password, site, comment, status))
        return self.c.lastrowid

    @async
    def deletePackage(self, pid):
        # order updated by trigger
        self.c.execute('DELETE FROM packages WHERE pid=?', (pid,))

    @async
    def deleteFile(self, fid, order, package):
        """ To delete a file order and package of it is needed """
        self.c.execute('DELETE FROM files WHERE fid=?', (fid,))
        self.c.execute('UPDATE files SET fileorder=fileorder-1 WHERE fileorder > ? AND package=?',
            (order, package))

    @async
    def saveCollector(self, owner, data):
        """ simply save the json string to database """
        self.c.execute("INSERT INTO collector(owner, data) VALUES (?,?)", (owner, data))

    @queue
    def retrieveCollector(self, owner):
        """ retrieve the saved string """
        self.c.execute('SELECT data FROM collector owner=?', (owner,))
        return self.c.fetchone()[0]

    @async
    def deleteCollector(self, owner):
        """ drop saved user collector """
        self.c.execute('DELETE FROM collector WHERE owner=?', (owner,))

    @queue
    def getAllFiles(self, package=None, search=None, unfinished=False):
        """ Return dict with file information

        :param package: optional package to filter out
        :param search: or search string for file name
        :param unfinished: filter by dlstatus not finished
        """
        qry = ('SELECT fid, name, size, status, media, added, fileorder, '
               'url, plugin, hash, dlstatus, error, package FROM files')

        if unfinished:
            qry += ' WHERE dlstatus NOT IN (0, 5, 6)'

        if package is not None:
            qry += ' AND' if unfinished else ' WHERE'
            self.c.execute(qry + ' package=? ORDER BY package, fileorder', (package,))
        elif search is not None:
            qry += ' AND' if unfinished else ' WHERE'
            search = "%%%s%%" % search.strip("%")
            self.c.execute(qry + ' name LIKE ? ORDER BY package, fileorder', (search,))

        else:
            self.c.execute(qry)

        data = OrderedDict()
        for r in self.c:
            f = FileInfo(r[0], r[1], r[12], r[2], r[3], r[4], r[5], r[6])
            if r[10] > 0: # dl status != NA
                f.download = DownloadInfo(r[7], r[8], r[9], r[10], self.manager.statusMsg[r[10]], r[11])

            data[r[0]] = f

        return data

    @queue
    def getAllPackages(self, root=None):
        """ Return dict with package information

        :param root: optional root to filter
        """
        qry = ('SELECT pid, name, folder, root, site, comment, password, added, status, packageorder '
               'FROM packages%s ORDER BY root, packageorder')

        if root is None:
            stats = self.getPackageStats()
            self.c.execute(qry % "")
        else:
            stats = self.getPackageStats(root=root)
            self.c.execute(qry % ' WHERE root=? OR pid=?', (root, root))

        data = OrderedDict()
        for r in self.c:
            data[r[0]] = PackageInfo(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], stats.get(r[0], default)
            )

        return data

    @inner
    def getPackageStats(self, pid=None, root=None):
        qry = ("SELECT p.pid, SUM(f.size) AS sizetotal, COUNT(f.fid) AS linkstotal, sizedone, linksdone "
               "FROM packages p JOIN files f ON p.pid = f.package AND f.dlstatus > 0 %(sub)s LEFT OUTER JOIN "
               "(SELECT p.pid AS pid, SUM(f.size) AS sizedone, COUNT(f.fid) AS linksdone "
               "FROM packages p JOIN files f ON p.pid = f.package %(sub)s AND f.dlstatus in (5,6) GROUP BY p.pid) s ON s.pid = p.pid "
               "GROUP BY p.pid")

        # status in (finished, skipped, processing)

        if root is not None:
            self.c.execute(qry % {"sub": "AND (p.root=:root OR p.pid=:root)"}, locals())
        elif pid is not None:
            self.c.execute(qry % {"sub": "AND p.pid=:pid"}, locals())
        else:
            self.c.execute(qry % {"sub": ""})

        data = {}
        for r in self.c:
            data[r[0]] = PackageStats(
                r[2] if r[2] else 0,
                r[4] if r[4] else 0,
                int(r[1]) if r[1] else 0,
                int(r[3]) if r[3] else 0,
            )

        return data

    @queue
    def getStatsForPackage(self, pid):
        return self.getPackageStats(pid=pid)[pid]

    @queue
    def getFileInfo(self, fid, force=False):
        """get data for specific file"""
        self.c.execute('SELECT fid, name, size, status, media, added, fileorder, '
                       'url, plugin, hash, dlstatus, error, package FROM files '
                       'WHERE fid=?', (fid,))
        r = self.c.fetchone()
        if not r:
            return None
        else:
            f = FileInfo(r[0], r[1], r[12], r[2], r[3], r[4], r[5], r[6])
            if r[10] > 0 or force:
                f.download = DownloadInfo(r[7], r[8], r[9], r[10], self.manager.statusMsg[r[10]], r[11])

            return f

    @queue
    def getPackageInfo(self, pid, stats=True):
        """get data for a specific package, optionally with package stats"""
        if stats:
            stats = self.getPackageStats(pid=pid)

        self.c.execute('SELECT pid, name, folder, root, site, comment, password, added, status, packageorder '
                       'FROM packages WHERE pid=?', (pid,))

        r = self.c.fetchone()
        if not r:
            return None
        else:
            return PackageInfo(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], stats.get(r[0], default) if stats else None
            )

    @async
    def updateLinkInfo(self, data):
        """ data is list of tuples (name, size, status,[ hash,] url)"""
        if data and len(data[0]) == 4:
            self.c.executemany('UPDATE files SET name=?, size=?, dlstatus=? WHERE url=? AND dlstatus IN (0,1,2,3,14)',
                data)
        else:
            self.c.executemany(
                'UPDATE files SET name=?, size=?, dlstatus=?, hash=? WHERE url=? AND dlstatus IN (0,1,2,3,14)', data)

    @async
    def updateFile(self, f):
        self.c.execute('UPDATE files SET name=?, size=?, status=?,'
                       'media=?, url=?, hash=?, dlstatus=?, error=? WHERE fid=?',
            (f.name, f.size, f.filestatus, f.media, f.url,
             f.hash, f.status, f.error, f.fid))

    @async
    def updatePackage(self, p):
        self.c.execute('UPDATE packages SET name=?, folder=?, site=?, comment=?, password=?, status=? WHERE pid=?',
            (p.name, p.folder, p.site, p.comment, p.password, p.status, p.pid))

    @async
    def orderPackage(self, pid, root, oldorder, order):
        if oldorder > order: # package moved upwards
            self.c.execute(
                'UPDATE packages SET packageorder=packageorder+1 WHERE packageorder >= ? AND packageorder < ? AND root=? AND packageorder >= 0'
                , (order, oldorder, root))
        elif oldorder < order: # moved downwards
            self.c.execute(
                'UPDATE packages SET packageorder=packageorder-1 WHERE packageorder <= ? AND packageorder > ? AND root=? AND packageorder >= 0'
                , (order, oldorder, root))

        self.c.execute('UPDATE packages SET packageorder=? WHERE pid=?', (order, pid))

    @async
    def orderFiles(self, pid, fids, oldorder, order):
        diff = len(fids)
        data = []

        if oldorder > order: # moved upwards
            self.c.execute('UPDATE files SET fileorder=fileorder+? WHERE fileorder >= ? AND fileorder < ? AND package=?'
                , (diff, order, oldorder, pid))
            data = [(order + i, fid) for i, fid in enumerate(fids)]
        elif oldorder < order:
            self.c.execute(
                'UPDATE files SET fileorder=fileorder-? WHERE fileorder <= ? AND fileorder >= ? AND package=?'
                , (diff, order, oldorder + diff, pid))
            data = [(order - diff + i + 1, fid) for i, fid in enumerate(fids)]

        self.c.executemany('UPDATE files SET fileorder=? WHERE fid=?', data)

    @async
    def moveFiles(self, pid, fids, package):
        self.c.execute('SELECT max(fileorder) FROM files WHERE package=?', (package,))
        r = self.c.fetchone()
        order = (r[0] if r[0] else 0) + 1

        self.c.execute('UPDATE files SET fileorder=fileorder-? WHERE fileorder > ? AND package=?',
            (len(fids), order, pid))

        data = [(package, order + i, fid) for i, fid in enumerate(fids)]
        self.c.executemany('UPDATE files SET package=?, fileorder=? WHERE fid=?', data)

    @async
    def movePackage(self, root, order, pid, dpid):
        self.c.execute('SELECT max(packageorder) FROM packages WHERE root=?', (dpid,))
        r = self.c.fetchone()
        max = (r[0] if r[0] else 0) + 1
        print max

        self.c.execute('SELECT pid, packageorder FROM packages WHERE root=?', (dpid,))
        for r in self.c:
            print r

        self.c.execute('UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > ? AND root=?',
            (order, root))

        self.c.execute('UPDATE packages SET root=?, packageorder=? WHERE pid=?', (dpid, max, pid))

    @async
    def restartFile(self, fid):
        # status -> queued
        self.c.execute('UPDATE files SET dlstatus=3, error="" WHERE fid=?', (fid,))

    @async
    def restartPackage(self, pid):
        # status -> queued
        self.c.execute('UPDATE files SET status=3 WHERE package=?', (pid,))

    @queue
    def getJob(self, occ):
        """return pyfile ids, which are suitable for download and dont use a occupied plugin"""
        cmd = "(%s)" % ", ".join(["'%s'" % x for x in occ])
        #TODO

        # dlstatus in online, queued | package status = ok
        cmd = ("SELECT f.fid FROM files as f INNER JOIN packages as p ON f.package=p.pid "
               "WHERE f.plugin NOT IN %s AND f.dlstatus IN (2,3) AND p.status=0 "
               "ORDER BY p.packageorder ASC, f.fileorder ASC LIMIT 5") % cmd

        self.c.execute(cmd) # very bad!

        return [x[0] for x in self.c]

    @queue
    def getUnfinished(self, pid):
        """return list of max length 3 ids with pyfiles in package not finished or processed"""

        # status in finished, skipped, processing
        self.c.execute("SELECT fid FROM files WHERE package=? AND dlstatus NOT IN (5, 6, 14) LIMIT 3", (pid,))
        return [r[0] for r in self.c]

    @queue
    def restartFailed(self):
        # status=queued, where status in failed, aborted, temp offline
        self.c.execute("UPDATE files SET dlstatus=3, error='' WHERE dlstatus IN (7, 11, 12)")

    @queue
    def findDuplicates(self, id, folder, filename):
        """ checks if filename exists with different id and same package """
        # TODO
        self.c.execute(
            "SELECT l.plugin FROM files f INNER JOIN packages as p ON f.package=p.pid AND p.folder=? WHERE f.fid!=? AND l.status=0 AND l.name=?"
            , (folder, id, filename))
        return self.c.fetchone()

    @queue
    def purgeLinks(self):
        # fstatus = missing
        self.c.execute("DELETE FROM files WHERE status == 1")

    @queue
    def purgeAll(self): # only used for debugging
        self.c.execute("DELETE FROM packages")
        self.c.execute("DELETE FROM files")
        self.c.execute("DELETE FROM collector")

FileMethods.register()