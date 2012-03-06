# -*- coding: utf-8 -*-

from collections import defaultdict

from helper.Stubs import Core
from helper.BenchmarkTest import BenchmarkTest

from module.database import DatabaseBackend

# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue

from random import choice

class TestDatabase(BenchmarkTest):
    bench = ["insert", "insert_links", "insert_many", "get_packages",
             "get_files", "get_files_queued", "get_package_childs", "get_package_files",
             "get_package_data", "get_file_data", "find_files", "collector", "purge"]
    pids = None
    fids = None

    @classmethod
    def setUpClass(cls):
        cls.pids = [-1]
        cls.fids = []

        cls.db = DatabaseBackend(Core())
        cls.db.manager = cls.db.core
        cls.db.manager.statusMsg = defaultdict(lambda: "statusmsg")

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
        self.fids = self.db.getAllFiles().keys()


    def test_insert(self, n=200):
        for i in range(n):
            pid = self.db.addPackage("name", "folder", choice(self.pids), "password", "site", "comment", 0)
            self.pids.append(pid)

    def test_insert_links(self):
        for i in range(10000):
            fid = self.db.addLink("url %s" % i, "name", "plugin", choice(self.pids))
            self.fids.append(fid)

    def test_insert_many(self):
        for pid in self.pids:
            self.db.addLinks([("url %s" % i, "plugin") for i in range(50)], pid)

    def test_get_packages(self):
        packs = self.db.getAllPackages()
        n = len(packs)
        assert n == len(self.pids) -1

        print "Fetched %d packages" % n
        self.assert_pack(choice(packs.values()))

    def test_get_files(self):
        files = self.db.getAllFiles()
        n = len(files)
        assert n >= len(self.pids)

        print "Fetched %d files" % n
        self.assert_file(choice(files.values()))

    def test_get_files_queued(self):
        files = self.db.getAllFiles(unfinished=True)
        print "Fetched %d files queued" % len(files)

    def test_delete(self):
        pid = choice(self.pids)
        self.db.deletePackage(pid)
        self.pids.remove(pid)

    def test_get_package_childs(self):
        pid = choice(self.pids)
        packs = self.db.getAllPackages(root=pid)

        print "Package %d has %d packages" % (pid, len(packs))
        self.assert_pack(choice(packs.values()))

    def test_get_package_files(self):
        pid = choice(self.pids)
        files = self.db.getAllFiles(package=pid)

        print "Package %d has %d files" % (pid, len(files))
        self.assert_file(choice(files.values()))

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
        print "Found %s files" % len(files)
        f = choice(files.values())

        assert "1" in f.name

    def test_collector(self):
        self.db.deleteCollector()
        assert not self.db.getCollector()

        self.db.addCollector("plugin", "package", [("name", 0, 0, "url %d" % i) for i in range(10)])
        coll = self.db.getCollector()
        assert len(coll) == 10
        assert coll[0].plugin == "plugin"
        assert coll[0].packagename == "package"
        assert coll[0].name == "name"
        assert "url" in coll[0].url

        self.db.deleteCollector(url="url 1")
        assert len(self.db.getCollector()) == 9
        self.db.deleteCollector(package="package")
        assert not self.db.getCollector()

    def test_purge(self):
        self.db.purgeLinks()

    def assert_file(self, f):
        try:
            assert f is not None
            self.assert_int(f, ("fid", "status", "size", "media", "fileorder", "added", "package"))
            assert f.status in range(5)
            assert f.media in range(1024)
            assert f.package in self.pids
            assert f.added > 10 ** 6 # date is usually big integer
        except:
            print f
            raise

    def assert_pack(self, p):
        try:
            assert p is not None
            self.assert_int(p, ("pid", "root", "added", "status", "packageorder"))
            assert p.pid in self.pids
            assert p.status in range(5)
            assert p.root in self.pids
            assert p.added > 10 ** 6
        except:
            print p
            raise

    def assert_int(self, obj, list):
        for attr in list: assert type(getattr(obj, attr)) == int

if __name__ == "__main__":
    TestDatabase.benchmark()