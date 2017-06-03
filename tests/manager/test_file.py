#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import random
from builtins import range

from future import standard_library

from pyload.core.database import DatabaseBackend
from pyload.core.datatype import DownloadState
from tests.helper.benchmark import BenchmarkTest
from tests.helper.stubs import Core, normal_user

standard_library.install_aliases()


# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue


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
        cls.db.purge_all()

        cls.m = cls.db.manager = c.files

    @classmethod
    def tearDownClass(cls):
        cls.db.purge_all()
        cls.db.shutdown()

    # benchmarker ignore setup
    def setUp(self):
        self.db.purge_all()
        self.pids = [-1]

        self.count = 20
        self.test_add_packages()
        self.test_add_files()

    def test_add_packages(self):
        for i in range(100):
            pid = self.manager.add_package("name", "folder", random.choice(
                self.pids), "", "", "", False, normal_user.uid)
            self.pids.append(pid)

        if -1 in self.pids:
            self.pids.remove(-1)

    def test_add_files(self):
        for pid in self.pids:
            self.manager.add_links(
                (("plugin {0:d}".format(i),
                  "url {0}".format(i)) for i in range(self.count)),
                pid, normal_user.uid)

        count = self.manager.get_queue_stats()[0]
        files = self.count * len(self.pids)
        # in test runner files get added twice
        assert count == files or count == files * 2

    def test_get(self):
        info = self.manager.get_package_info(random.choice(self.pids))
        assert info.stats.linkstotal == self.count

        fid = random.choice(info.fids)
        file = self.manager.get_file(fid)
        assert file.fid in self.manager.files

        file.name = "new name"
        file.sync()
        finfo = self.manager.get_file_info(fid)
        assert finfo is not None
        assert finfo.name == "new name"

        pack = self.manager.get_package(random.choice(self.pids))
        assert pack is not None
        assert pack.pid in self.manager.packages
        pack.sync()

        pack.delete()

        self.manager.get_tree(-1, True, None)

    def test_get_filtered(self):
        all = self.manager.get_tree(-1, True, None)
        finished = self.manager.get_tree(-1, True, DownloadState.Finished)
        unfinished = self.manager.get_tree(-1, True, DownloadState.Unfinished)

        assert len(finished.files) + \
            len(unfinished.files) == len(
                all.files) == self.manager.db.filecount()

    def test_get_files_root(self):
        view = self.manager.get_tree(-1, True, None)

        for pid in self.pids:
            assert pid in view.packages

        assert len(view.packages) == len(self.pids)

        pack = random.choice(view.packages.values())
        assert len(pack.fids) == self.count
        assert pack.stats.linkstotal == self.count

    def test_get_package_content(self):
        view = self.manager.get_tree(random.choice(self.pids), False, None)
        p = view.root

        assert len(view.packages) == len(p.pids)
        for pid in p.pids:
            assert pid in view.packages

    def test_get_package_tree(self):
        view = self.manager.get_tree(random.choice(self.pids), True, None)
        for pid in view.root.pids:
            assert pid in view.packages
        for fid in view.root.fids:
            assert fid in view.files

    def test_delete(self):
        self.manager.remove_file(self.count * 5)
        self.manager.remove_package(random.choice(self.pids))

    def test_order_package(self):
        parent = self.manager.add_package(
            "order", "", -1, "", "", "", False, normal_user.uid)
        self.manager.add_links((("url", "plugin")
                                for i in range(100)), parent, normal_user.uid)

        pids = [
            self.manager.add_package(
                "c", "", parent, "", "", "", False, normal_user.uid)
            for i in range(5)]
        v = self.manager.get_tree(parent, False, None)
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
        parent = self.manager.add_package(
            "order", "", -1, "", "", "", False, normal_user.uid)
        self.manager.add_links((("url", "plugin")
                                for i in range(100)), parent, normal_user.uid)
        v = self.manager.get_tree(parent, False, None)

        fids = v.root.fids[10:20]
        v = self.assert_files_ordered(parent, fids, 0)

        fids = v.root.fids[20:30]

        self.manager.order_files(fids, parent, 99)
        v = self.manager.get_tree(parent, False, None)
        assert fids[-1] == v.root.fids[-1]
        assert fids[0] == v.root.fids[90]
        self.assert_ordered(fids, 90, 100, v.root.fids, v.files)

        fids = v.root.fids[80:]
        v = self.assert_files_ordered(parent, fids, 20)

        self.manager.order_files(fids, parent, 80)
        v = self.manager.get_tree(parent, False, None)
        self.assert_ordered(fids, 61, 81, v.root.fids, v.files)

        fids = v.root.fids[50:51]
        self.manager.order_files(fids, parent, 99)
        v = self.manager.get_tree(parent, False, None)
        self.assert_ordered(fids, 99, 100, v.root.fids, v.files)

        fids = v.root.fids[50:51]
        v = self.assert_files_ordered(parent, fids, 0)

    def assert_files_ordered(self, parent, fids, pos):
        assert [self.manager.get_file(random.choice(fids)) for i in range(5)]
        self.manager.order_files(fids, parent, pos)
        v = self.manager.get_tree(parent, False, False)
        self.assert_ordered(fids, pos, pos + len(fids), v.root.fids, v.files)

        return v

    def assert_pack_ordered(self, parent, pid, pos):
        self.manager.order_package(pid, pos)
        v = self.manager.get_tree(parent, False, False)
        self.assert_ordered([pid], pos, pos + 1, v.root.pids, v.packages, True)

    # assert that ordering is total, complete with no gaps
    def assert_ordered(self, part, start, end, data, dict, pack=False):
        assert data[start:end] == part
        if pack:
            assert sorted(pinfo.packageorder for pinfo in dict.values()
                          ) == list(range(len(dict)))
            assert [dict[pid].packageorder for pid in part] == list(
                range(start, end))
        else:
            assert sorted(finfo.fileorder for finfo in dict.values()
                          ) == list(range(len(dict)))
            assert [dict[fid].fileorder for fid in part] == list(
                range(start, end))

    def test_move(self):

        pid = self.pids[-1]
        pid2 = self.pids[1]

        self.manager.move_package(pid, -1)
        v = self.manager.get_tree(-1, False, False)

        assert pid in v.root.pids
        assert sorted(pinfo.packageorder for pinfo in v.packages.values()
                      ) == list(range(len(v.packages)))

        v = self.manager.get_tree(pid, False, False)
        fids = v.root.fids[10:20]
        self.manager.move_files(fids, pid2)
        v = self.manager.get_tree(pid2, False, False)

        assert sorted(finfo.fileorder for finfo in v.files.values()
                      ) == list(range(len(v.files)))
        assert len(v.files) == self.count + len(fids)


if __name__ == '__main__':
    TestFileManager.benchmark()
