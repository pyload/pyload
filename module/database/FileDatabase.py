#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2012 pyLoad Team
#   http://www.pyload.org
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from new_collections import OrderedDict

from module.Api import DownloadInfo, FileInfo, PackageInfo, PackageStats, DownloadState as DS, state_string
from module.database import DatabaseMethods, queue, async, inner

zero_stats = PackageStats(0, 0, 0, 0)

class FileMethods(DatabaseMethods):
    @queue
    def filecount(self, user=None):
        """returns number of files"""
        self.c.execute("SELECT COUNT(*) FROM files")
        return self.c.fetchone()[0]

    @queue
    def downloadcount(self, user=None):
        """ number of downloads """
        self.c.execute("SELECT COUNT(*) FROM files WHERE dlstatus != 0")
        return self.c.fetchone()[0]

    @queue
    def queuecount(self, user=None):
        """ number of files in queue not finished yet"""
        # status not in NA, finished, skipped
        self.c.execute("SELECT COUNT(*) FROM files WHERE dlstatus NOT IN (0,5,6)")
        return self.c.fetchone()[0]

    @queue
    def processcount(self, fid=-1, user=None):
        """ number of files which have to be processed """
        # status in online, queued, starting, waiting, downloading
        self.c.execute("SELECT COUNT(*) FROM files WHERE dlstatus IN (2,3,8,9,10) AND fid != ?", (fid, ))
        return self.c.fetchone()[0]

    # TODO: think about multiuser side effects on *count methods

    @queue
    def addLink(self, url, name, plugin, package, owner):
        # mark file status initially as missing, dlstatus - queued
        self.c.execute('INSERT INTO files(url, name, plugin, status, dlstatus, package, owner) VALUES(?,?,?,1,3,?,?)',
            (url, name, plugin, package, owner))
        return self.c.lastrowid

    @async
    def addLinks(self, links, package, owner):
        """ links is a list of tuples (url, plugin)"""
        links = [(x[0], x[0], x[1], package, owner) for x in links]
        self.c.executemany('INSERT INTO files(url, name, plugin, status, dlstatus, package, owner) VALUES(?,?,?,1,3,?,?)',
            links)

    @queue
    def addFile(self, name, size, media, package, owner):
        # file status - ok, dl status NA
        self.c.execute('INSERT INTO files(name, size, media, package, owner) VALUES(?,?,?,?,?)',
            (name, size, media, package, owner))
        return self.c.lastrowid

    @queue
    def addPackage(self, name, folder, root, password, site, comment, status, owner):
        self.c.execute(
            'INSERT INTO packages(name, folder, root, password, site, comment, status, owner) VALUES(?,?,?,?,?,?,?,?)'
            , (name, folder, root, password, site, comment, status, owner))
        return self.c.lastrowid

    @async
    def deletePackage(self, pid, owner=None):
        # order updated by trigger, as well as links deleted
        if owner is None:
            self.c.execute('DELETE FROM packages WHERE pid=?', (pid,))
        else:
            self.c.execute('DELETE FROM packages WHERE pid=? AND owner=?', (pid, owner))

    @async
    def deleteFile(self, fid, order, package, owner=None):
        """ To delete a file order and package of it is needed """
        if owner is None:
            self.c.execute('DELETE FROM files WHERE fid=?', (fid,))
            self.c.execute('UPDATE files SET fileorder=fileorder-1 WHERE fileorder > ? AND package=?',
                (order, package))
        else:
            self.c.execute('DELETE FROM files WHERE fid=? AND owner=?', (fid, owner))
            self.c.execute('UPDATE files SET fileorder=fileorder-1 WHERE fileorder > ? AND package=? AND owner=?',
                (order, package, owner))

    @async
    def saveCollector(self, owner, data):
        """ simply save the json string to database """
        self.c.execute("INSERT INTO collector(owner, data) VALUES (?,?)", (owner, data))

    @queue
    def retrieveCollector(self, owner):
        """ retrieve the saved string """
        self.c.execute('SELECT data FROM collector WHERE owner=?', (owner,))
        r = self.c.fetchone()
        if not r: return None
        return r[0]

    @async
    def deleteCollector(self, owner):
        """ drop saved user collector """
        self.c.execute('DELETE FROM collector WHERE owner=?', (owner,))

    @queue
    def getAllFiles(self, package=None, search=None, state=None, owner=None):
        """ Return dict with file information

        :param package: optional package to filter out
        :param search: or search string for file name
        :param unfinished: filter by dlstatus not finished
        :param owner: only specific owner
        """
        qry = ('SELECT fid, name, owner, size, status, media, added, fileorder, '
               'url, plugin, hash, dlstatus, error, package FROM files WHERE ')

        arg = []

        if state is not None and state != DS.All:
            qry += 'dlstatus IN (%s) AND ' %  state_string(state)
        if owner is not None:
            qry += 'owner=? AND '
            arg.append(owner)

        if package is not None:
            arg.append(package)
            qry += 'package=? AND '
        if search is not None:
            search = "%%%s%%" % search.strip("%")
            arg.append(search)
            qry += "name LIKE ? "

        # make qry valid
        if qry.endswith("WHERE "): qry = qry[:-6]
        if qry.endswith("AND "): qry = qry[:-4]

        self.c.execute(qry + "ORDER BY package, fileorder", arg)

        data = OrderedDict()
        for r in self.c:
            f = FileInfo(r[0], r[1], r[13], r[2], r[3], r[4], r[5], r[6], r[7])
            if r[11] > 0: # dl status != NA
                f.download = DownloadInfo(r[8], r[9], r[10], r[11], self.manager.statusMsg[r[11]], r[12])

            data[r[0]] = f

        return data

    @queue
    def getAllPackages(self, root=None, owner=None, tags=None):
        """ Return dict with package information

        :param root: optional root to filter
        :param owner: optional user id
        :param tags: optional tag list
        """
        qry = ('SELECT pid, name, folder, root, owner, site, comment, password, added, tags, status, packageorder '
               'FROM packages%s ORDER BY root, packageorder')

        if root is None:
            stats = self.getPackageStats(owner=owner)
            if owner is None:
                self.c.execute(qry % "")
            else:
                self.c.execute(qry % " WHERE owner=?", (owner,))
        else:
            stats = self.getPackageStats(root=root, owner=owner)
            if owner is None:
                self.c.execute(qry % ' WHERE root=? OR pid=?', (root, root))
            else:
                self.c.execute(qry % ' WHERE (root=? OR pid=?) AND owner=?', (root, root, owner))

        data = OrderedDict()
        for r in self.c:
            data[r[0]] = PackageInfo(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9].split(","), r[10], r[11], stats.get(r[0], zero_stats)
            )

        return data

    @inner
    def getPackageStats(self, pid=None, root=None, owner=None):
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
        elif owner is not None:
            self.c.execute(qry % {"sub": "AND p.owner=:owner"}, locals())
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
        """get data for specific file, when force is true download info will be appended"""
        self.c.execute('SELECT fid, name, owner, size, status, media, added, fileorder, '
                       'url, plugin, hash, dlstatus, error, package FROM files '
                       'WHERE fid=?', (fid,))
        r = self.c.fetchone()
        if not r:
            return None
        else:
            f = FileInfo(r[0], r[1], r[13], r[2], r[3], r[4], r[5], r[6], r[7])
            if r[11] > 0 or force:
                f.download = DownloadInfo(r[8], r[9], r[10], r[11], self.manager.statusMsg[r[11]], r[12])

            return f

    @queue
    def getPackageInfo(self, pid, stats=True):
        """get data for a specific package, optionally with package stats"""
        if stats:
            stats = self.getPackageStats(pid=pid)

        self.c.execute('SELECT pid, name, folder, root, owner, site, comment, password, added, tags, status, packageorder '
                       'FROM packages WHERE pid=?', (pid,))

        r = self.c.fetchone()
        if not r:
            return None
        else:
            return PackageInfo(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9].split(","), r[10], r[11], stats.get(r[0], zero_stats) if stats else None
            )

    @async
    def updateLinkInfo(self, data, owner):
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
        self.c.execute('UPDATE packages SET name=?, folder=?, site=?, comment=?, password=?, tags=?, status=? WHERE pid=?',
            (p.name, p.folder, p.site, p.comment, p.password, ",".join(p.tags), p.status, p.pid))

    # TODO: most modifying methods needs owner argument to avoid checking beforehand
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


    # TODO: multi user approach
    @queue
    def getJob(self, occ):
        """return pyfile ids, which are suitable for download and don't use a occupied plugin"""
        cmd = "(%s)" % ", ".join(["'%s'" % x for x in occ])
        #TODO

        # dlstatus in online, queued | package status = ok
        cmd = ("SELECT f.fid FROM files as f INNER JOIN packages as p ON f.package=p.pid "
               "WHERE f.plugin NOT IN %s AND f.dlstatus IN (2,3) AND p.status=0 "
               "ORDER BY p.packageorder ASC, f.fileorder ASC LIMIT 5") % cmd

        self.c.execute(cmd)

        return [x[0] for x in self.c]

    @queue
    def getUnfinished(self, pid):
        """return list of max length 3 ids with pyfiles in package not finished or processed"""

        # status in finished, skipped, processing
        self.c.execute("SELECT fid FROM files WHERE package=? AND dlstatus NOT IN (5, 6, 14) LIMIT 3", (pid,))
        return [r[0] for r in self.c]

    @queue
    def restartFailed(self, owner):
        # status=queued, where status in failed, aborted, temp offline
        self.c.execute("UPDATE files SET dlstatus=3, error='' WHERE dlstatus IN (7, 11, 12)")

    @queue
    def findDuplicates(self, id, folder, filename):
        """ checks if filename exists with different id and same package, dlstatus = finished """
        # TODO: also check root of package
        self.c.execute(
            "SELECT f.plugin FROM files f INNER JOIN packages as p ON f.package=p.pid AND p.folder=? WHERE f.fid!=? AND f.dlstatus=5 AND f.name=?"
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