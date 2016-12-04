#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from tests.helper.Stubs import Core
from tests.helper.BenchmarkTest import BenchmarkTest

from pyload.Api import DownloadState, PackageInfo, FileInfo
from pyload.database import DatabaseBackend

# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue

from random import choice


class TestDatabase(BenchmarkTest):
    bench = ["insert", "insert_links", "insert_many", "get_packages",
             "get_files", "get_files_queued", "get_package_childs", "get_package_files",
             "get_package_data", "get_file_data", "find_files", "collector", "purge"]
    pids = None
    fids = None
    owner = 123
    pstatus = 0

    @classmethod
    def setUpClass(cls):
        cls.pids = [-1]
        cls.fids = []

        cls.db = DatabaseBackend(Core())
        cls.db.manager = cls.db.core

        cls.db.setup()
        cls.db.purgeAll()

    @classmethod
    def tearDownClass(cls):
        cls.db.purgeAll()
        cls.db.shutdown()

    # benchmarker ignore setup
    def setUp(self):
        self.db.purgeAll()
        self.pids = [-1]
        self.fids = []

        self.test_insert(20)
        self.test_insert_many()
        self.fids = list(self.db.getAllFiles().keys())


    def test_insert(self, n=200):
        for i in range(n):
            pid = self.db.addPackage("name", "folder", choice(self.pids), "password", "site", "comment", self.pstatus,
                self.owner)
            self.pids.append(pid)

    def test_insert_links(self):
        for i in range(10000):
            fid = self.db.addLink("url %s" % i, "name", "plugin", choice(self.pids), self.owner)
            self.fids.append(fid)

    def test_insert_many(self):
        for pid in self.pids:
            self.db.addLinks([("url %s" % i, "plugin") for i in range(50)], pid, self.owner)

    def test_get_packages(self):
        packs = self.db.getAllPackages()
        n = len(packs)
        assert n == len(self.pids) - 1

        print("Fetched %d packages" % n)
        self.assert_pack(choice(list(packs.values())))

    def test_get_files(self):
        files = self.db.getAllFiles()
        n = len(files)
        assert n >= len(self.pids)

        print("Fetched %d files" % n)
        self.assert_file(choice(list(files.values())))

    def test_get_files_queued(self):
        files = self.db.getAllFiles(state=DownloadState.Unfinished)
        print("Fetched %d files queued" % len(files))

    def test_delete(self):
        pid = choice(self.pids)
        self.db.deletePackage(pid)
        self.pids.remove(pid)

    def test_get_package_childs(self):
        pid = choice(self.pids)
        packs = self.db.getAllPackages(root=pid)

        print("Package %d has %d packages" % (pid, len(packs)))
        self.assert_pack(choice(list(packs.values())))

    def test_get_package_files(self):
        pid = choice(self.pids)
        files = self.db.getAllFiles(package=pid)

        print("Package %d has %d files" % (pid, len(files)))
        self.assert_file(choice(list(files.values())))

    def test_get_package_data(self, stats=False):
        pid = choice(self.pids)
        p = self.db.getPackageInfo(pid, stats)
        self.assert_pack(p)
        # test again with stat
        if not stats:
            self.test_get_package_data(True)

    def test_get_file_data(self):
        fid = choice(self.fids)
        f = self.db.getFileInfo(fid)
        self.assert_file(f)

    def test_find_files(self):
        files = self.db.getAllFiles(search="1")
        print("Found %s files" % len(files))
        f = choice(list(files.values()))

        assert "1" in f.name
        names = self.db.getMatchingFilenames("1")
        for name in names:
            assert "1" in name

    def test_collector(self):
        self.db.saveCollector(0, "data")
        assert self.db.retrieveCollector(0) == "data"
        self.db.deleteCollector(0)

    def test_purge(self):
        self.db.purgeLinks()


    def test_user_context(self):
        self.db.purgeAll()

        p1 = self.db.addPackage("name", "folder", 0, "password", "site", "comment", self.pstatus, 0)
        self.db.addLink("url", "name", "plugin", p1, 0)
        p2 = self.db.addPackage("name", "folder", 0, "password", "site", "comment", self.pstatus, 1)
        self.db.addLink("url", "name", "plugin", p2, 1)

        assert len(self.db.getAllPackages(owner=0)) == 1 == len(self.db.getAllFiles(owner=0))
        assert len(self.db.getAllPackages(root=0, owner=0)) == 1 == len(self.db.getAllFiles(package=p1, owner=0))
        assert len(self.db.getAllPackages(owner=1)) == 1 == len(self.db.getAllFiles(owner=1))
        assert len(self.db.getAllPackages(root=0, owner=1)) == 1 == len(self.db.getAllFiles(package=p2, owner=1))
        assert len(self.db.getAllPackages()) == 2 == len(self.db.getAllFiles())

        self.db.deletePackage(p1, 1)
        assert len(self.db.getAllPackages(owner=0)) == 1 == len(self.db.getAllFiles(owner=0))
        self.db.deletePackage(p1, 0)
        assert len(self.db.getAllPackages(owner=1)) == 1 == len(self.db.getAllFiles(owner=1))
        self.db.deletePackage(p2)

        assert len(self.db.getAllPackages()) == 0

    def test_count(self):
        self.db.purgeAll()

        assert self.db.downloadstats() == (0, 0)
        assert self.db.queuestats() == (0, 0)
        assert self.db.processcount() == 0

    def test_update(self):
        p1 = self.db.addPackage("name", "folder", 0, "password", "site", "comment", self.pstatus, 0)
        pack = self.db.getPackageInfo(p1)
        assert isinstance(pack, PackageInfo)

        pack.folder = "new folder"
        pack.comment = "lol"
        pack.tags.append("video")

        self.db.updatePackage(pack)

        pack = self.db.getPackageInfo(p1)
        assert pack.folder == "new folder"
        assert pack.comment == "lol"
        assert "video" in pack.tags

    def assert_file(self, f):
        try:
            assert f is not None
            assert isinstance(f, FileInfo)
            self.assert_int(f, ("fid", "status", "size", "media", "fileorder", "added", "package", "owner"))
            assert f.status in range(5)
            assert f.owner == self.owner
            assert f.media in range(1024)
            assert f.package in self.pids
            assert f.added > 10 ** 6 # date is usually big integer
        except Exception:
            print(f)
            raise

    def assert_pack(self, p):
        try:
            assert p is not None
            assert isinstance(p, PackageInfo)
            self.assert_int(p, ("pid", "root", "added", "status", "packageorder", "owner"))
            assert p.pid in self.pids
            assert p.owner == self.owner
            assert p.status in range(5)
            assert p.root in self.pids
            assert p.added > 10 ** 6
            assert isinstance(p.tags, list)
            assert p.shared in (0, 1)
        except Exception:
            print(p)
            raise

    def assert_int(self, obj, list):
        for attr in list: assert isinstance(getattr(obj, attr), int)

if __name__ == "__main__":
    TestDatabase.benchmark()
