#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from builtins import range
from random import choice

from future import standard_library

from pyload.api import DownloadState, FileInfo, PackageInfo
from pyload.database import DatabaseBackend
from tests.helper.benchmark import BenchmarkTest
from tests.helper.stubs import Core

standard_library.install_aliases()


# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue


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
        cls.db.purge_all()

    @classmethod
    def tearDownClass(cls):
        cls.db.purge_all()
        cls.db.shutdown()

    # benchmarker ignore setup
    def setUp(self):
        self.db.purge_all()
        self.pids = [-1]
        self.fids = []

        self.test_insert(20)
        self.test_insert_many()
        self.fids = list(self.db.get_all_files().keys())

    def test_insert(self, n=200):
        for i in range(n):
            pid = self.db.add_package("name", "folder", choice(self.pids), "password", "site", "comment", self.pstatus,
                                      self.owner)
            self.pids.append(pid)

    def test_insert_links(self):
        for i in range(10000):
            fid = self.db.add_link("url {}".format(
                i), "name", "plugin", choice(self.pids), self.owner)
            self.fids.append(fid)

    def test_insert_many(self):
        for pid in self.pids:
            self.db.add_links((("url {}".format(i), "plugin")
                               for i in range(50)), pid, self.owner)

    def test_get_packages(self):
        packs = self.db.get_all_packages()
        n = len(packs)
        assert n == len(self.pids) - 1

        print("Fetched {:d} packages".format(n))
        self.assert_pack(choice(packs.values()))

    def test_get_files(self):
        files = self.db.get_all_files()
        n = len(files)
        assert n >= len(self.pids)

        print("Fetched {:d} files".format(n))
        self.assert_file(choice(files.values()))

    def test_get_files_queued(self):
        files = self.db.get_all_files(state=DownloadState.Unfinished)
        print("Fetched {:d} files queued".format(len(files)))

    def test_delete(self):
        pid = choice(self.pids)
        self.db.delete_package(pid)
        self.pids.remove(pid)

    def test_get_package_childs(self):
        pid = choice(self.pids)
        packs = self.db.get_all_packages(root=pid)

        print("Package {:d} has {:d} packages".format(pid, len(packs)))
        self.assert_pack(choice(packs.values()))

    def test_get_package_files(self):
        pid = choice(self.pids)
        files = self.db.get_all_files(package=pid)

        print("Package {:d} has {:d} files".format(pid, len(files)))
        self.assert_file(choice(files.values()))

    def test_get_package_data(self, stats=False):
        pid = choice(self.pids)
        p = self.db.get_package_info(pid, stats)
        self.assert_pack(p)
        # test again with stat
        if not stats:
            self.test_get_package_data(True)

    def test_get_file_data(self):
        fid = choice(self.fids)
        f = self.db.get_file_info(fid)
        self.assert_file(f)

    def test_find_files(self):
        files = self.db.get_all_files(search="1")
        print("Found {} files".format(len(files)))
        f = choice(files.values())

        assert "1" in f.name
        names = self.db.get_matching_filenames("1")
        for name in names:
            assert "1" in name

    def test_collector(self):
        self.db.save_collector(0, "data")
        assert self.db.retrieve_collector(0) == "data"
        self.db.delete_collector(0)

    def test_purge(self):
        self.db.purge_links()

    def test_user_context(self):
        self.db.purge_all()

        p1 = self.db.add_package(
            "name", "folder", 0, "password", "site", "comment", self.pstatus, 0)
        self.db.add_link("url", "name", "plugin", p1, 0)
        p2 = self.db.add_package(
            "name", "folder", 0, "password", "site", "comment", self.pstatus, 1)
        self.db.add_link("url", "name", "plugin", p2, 1)

        assert len(self.db.get_all_packages(owner=0)) == 1 == len(
            self.db.get_all_files(owner=0))
        assert len(self.db.get_all_packages(root=0, owner=0)) == 1 == len(
            self.db.get_all_files(package=p1, owner=0))
        assert len(self.db.get_all_packages(owner=1)) == 1 == len(
            self.db.get_all_files(owner=1))
        assert len(self.db.get_all_packages(root=0, owner=1)) == 1 == len(
            self.db.get_all_files(package=p2, owner=1))
        assert len(self.db.get_all_packages()) == 2 == len(
            self.db.get_all_files())

        self.db.delete_package(p1, 1)
        assert len(self.db.get_all_packages(owner=0)) == 1 == len(
            self.db.get_all_files(owner=0))
        self.db.delete_package(p1, 0)
        assert len(self.db.get_all_packages(owner=1)) == 1 == len(
            self.db.get_all_files(owner=1))
        self.db.delete_package(p2)

        assert len(self.db.get_all_packages()) == 0

    def test_count(self):
        self.db.purge_all()

        assert self.db.downloadstats() == (0, 0)
        assert self.db.queuestats() == (0, 0)
        assert self.db.processcount() == 0

    def test_update(self):
        p1 = self.db.add_package(
            "name", "folder", 0, "password", "site", "comment", self.pstatus, 0)
        pack = self.db.get_package_info(p1)
        assert isinstance(pack, PackageInfo)

        pack.folder = "new folder"
        pack.comment = "lol"
        pack.tags.append("video")

        self.db.update_package(pack)

        pack = self.db.get_package_info(p1)
        assert pack.folder == "new folder"
        assert pack.comment == "lol"
        assert "video" in pack.tags

    def assert_file(self, f):
        try:
            assert f is not None
            assert isinstance(f, FileInfo)
            self.assert_in(f, ("fid", "status", "size", "media",
                               "fileorder", "added", "package", "owner"))
            assert f.status in range(5)
            assert f.owner == self.owner
            assert f.media in range(1024)
            assert f.package in self.pids
            assert f.added > 10 ** 6  #: date is usually big integer
        except Exception:
            print(f)
            raise

    def assert_pack(self, p):
        try:
            assert p is not None
            assert isinstance(p, PackageInfo)
            self.assert_in(p, ("pid", "root", "added",
                               "status", "packageorder", "owner"))
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

    def assert_in(self, obj, list):
        for attr in list:
            assert isinstance(getattr(obj, attr), int)

if __name__ == "__main__":
    TestDatabase.benchmark()
