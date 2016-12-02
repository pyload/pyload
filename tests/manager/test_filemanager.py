# -*- coding: utf-8 -*-

from random import choice

from tests.helper.Stubs import Core, normalUser
from tests.helper.BenchmarkTest import BenchmarkTest

from pyload.database import DatabaseBackend
# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue

from pyload.Api import DownloadState

class TestFileManager(BenchmarkTest):
    bench = ["add_packages", "add_files", "get_files_root", "get",
             "get_package_content", "get_package_tree",
             "order_package", "order_files", "move"]

    pids = [-1]
    count = 100

    @classmethod
    def setUpClass(cls):
        c = Core()
        # db needs separate initialisation
        cls.db = c.db
        cls.db.purgeAll()

        cls.m = cls.db.manager = c.files

    @classmethod
    def tearDownClass(cls):
        cls.db.purgeAll()
        cls.db.shutdown()

    # benchmarker ignore setup
    def setUp(self):
        self.db.purgeAll()
        self.pids = [-1]

        self.count = 20
        self.test_add_packages()
        self.test_add_files()

    def test_add_packages(self):
        for i in range(100):
            pid = self.m.addPackage("name", "folder", choice(self.pids), "", "", "", False, normalUser.uid)
            self.pids.append(pid)

        if -1 in self.pids:
            self.pids.remove(-1)

    def test_add_files(self):
        for pid in self.pids:
            self.m.addLinks([("plugin %d" % i, "url %s" % i) for i in range(self.count)], pid, normalUser.uid)

        count = self.m.getQueueStats()[0]
        files = self.count * len(self.pids)
        # in test runner files get added twice
        assert count == files or count == files * 2

    def test_get(self):
        info = self.m.getPackageInfo(choice(self.pids))
        assert info.stats.linkstotal == self.count

        fid = choice(info.fids)
        f = self.m.getFile(fid)
        assert f.fid in self.m.files

        f.name = "new name"
        f.sync()
        finfo = self.m.getFileInfo(fid)
        assert finfo is not None
        assert finfo.name == "new name"

        p = self.m.getPackage(choice(self.pids))
        assert p is not None
        assert p.pid in self.m.packages
        p.sync()

        p.delete()

        self.m.getTree(-1, True, None)

    def test_get_filtered(self):
        all = self.m.getTree(-1, True, None)
        finished = self.m.getTree(-1, True, DownloadState.Finished)
        unfinished = self.m.getTree(-1, True, DownloadState.Unfinished)

        assert len(finished.files) + len(unfinished.files) == len(all.files) == self.m.db.filecount()


    def test_get_files_root(self):
        view = self.m.getTree(-1, True, None)

        for pid in self.pids:
            assert pid in view.packages

        assert len(view.packages) == len(self.pids)

        p = choice(view.packages.values())
        assert len(p.fids) == self.count
        assert p.stats.linkstotal == self.count


    def test_get_package_content(self):
        view = self.m.getTree(choice(self.pids), False, None)
        p = view.root

        assert len(view.packages) == len(p.pids)
        for pid in p.pids: assert pid in view.packages

    def test_get_package_tree(self):
        view = self.m.getTree(choice(self.pids), True, None)
        for pid in view.root.pids: assert pid in view.packages
        for fid in view.root.fids: assert fid in view.files

    def test_delete(self):
        self.m.removeFile(self.count * 5)
        self.m.removePackage(choice(self.pids))

    def test_order_package(self):
        parent = self.m.addPackage("order", "", -1, "", "", "", False, normalUser.uid)
        self.m.addLinks([("url", "plugin") for i in range(100)], parent, normalUser.uid)

        pids = [self.m.addPackage("c", "", parent, "", "", "", False, normalUser.uid) for i in range(5)]
        v = self.m.getTree(parent, False, None)
        self.assert_ordered(pids, 0, 5, v.root.pids, v.packages, True)

        pid = v.packages.keys()[0]
        self.assert_pack_ordered(parent, pid, 3)
        self.assert_pack_ordered(parent, pid, 0)
        self.assert_pack_ordered(parent, pid, 0)
        self.assert_pack_ordered(parent, pid, 4)
        pid = v.packages.keys()[2]
        self.assert_pack_ordered(parent, pid, 4)
        self.assert_pack_ordered(parent, pid, 3)
        self.assert_pack_ordered(parent, pid, 2)


    def test_order_files(self):
        parent = self.m.addPackage("order", "", -1, "", "", "", False, normalUser.uid)
        self.m.addLinks([("url", "plugin") for i in range(100)], parent, normalUser.uid)
        v = self.m.getTree(parent, False, None)

        fids = v.root.fids[10:20]
        v = self.assert_files_ordered(parent, fids, 0)

        fids = v.root.fids[20:30]

        self.m.orderFiles(fids, parent, 99)
        v = self.m.getTree(parent, False, None)
        assert fids[-1] == v.root.fids[-1]
        assert fids[0] == v.root.fids[90]
        self.assert_ordered(fids, 90, 100, v.root.fids, v.files)

        fids = v.root.fids[80:]
        v = self.assert_files_ordered(parent, fids, 20)

        self.m.orderFiles(fids, parent, 80)
        v = self.m.getTree(parent, False, None)
        self.assert_ordered(fids, 61, 81, v.root.fids, v.files)

        fids = v.root.fids[50:51]
        self.m.orderFiles(fids, parent, 99)
        v = self.m.getTree(parent, False, None)
        self.assert_ordered(fids, 99, 100, v.root.fids, v.files)

        fids = v.root.fids[50:51]
        v = self.assert_files_ordered(parent, fids, 0)


    def assert_files_ordered(self, parent, fids, pos):
        fs = [self.m.getFile(choice(fids)) for i in range(5)]
        self.m.orderFiles(fids, parent, pos)
        v = self.m.getTree(parent, False, False)
        self.assert_ordered(fids, pos, pos+len(fids), v.root.fids, v.files)

        return v

    def assert_pack_ordered(self, parent, pid, pos):
        self.m.orderPackage(pid, pos)
        v = self.m.getTree(parent, False, False)
        self.assert_ordered([pid], pos, pos+1, v.root.pids, v.packages, True)

    # assert that ordering is total, complete with no gaps
    def assert_ordered(self, part, start, end, data, dict, pack=False):
        assert data[start:end] == part
        if pack:
            assert sorted([p.packageorder for p in dict.values()]) == range(len(dict))
            assert [dict[pid].packageorder for pid in part] == range(start, end)
        else:
            assert sorted([f.fileorder for f in dict.values()]) == range(len(dict))
            assert [dict[fid].fileorder for fid in part] == range(start, end)


    def test_move(self):

        pid = self.pids[-1]
        pid2 = self.pids[1]

        self.m.movePackage(pid, -1)
        v = self.m.getTree(-1, False, False)

        assert pid in v.root.pids
        assert sorted([p.packageorder for p in v.packages.values()]) == range(len(v.packages))

        v = self.m.getTree(pid, False, False)
        fids = v.root.fids[10:20]
        self.m.moveFiles(fids, pid2)
        v = self.m.getTree(pid2, False, False)

        assert sorted([f.fileorder for f in v.files.values()]) == range(len(v.files))
        assert len(v.files) == self.count + len(fids)



if __name__ == "__main__":
    TestFileManager.benchmark()
