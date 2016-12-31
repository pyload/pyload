#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import range
from tests.helper.stubs import Core, normalUser, adminUser, otherUser
from tests.helper.benchmarktest import BenchmarkTest

from pyload.database import DatabaseBackend
# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue


class TestDownloadManager(BenchmarkTest):

    bench = ["add_links", "simple", "empty"]

    USER = 2
    PACKAGES = 10
    LINKS = 50
    PLUGINS = 10

    @classmethod
    def setUpClass(cls):
        cls.c = Core()
        cls.db = cls.c.db
        cls.db.purgeAll()
        cls.db.addDebugUser(normalUser.uid)
        cls.db.addDebugUser(adminUser.uid)
        cls.db.addDebugUser(otherUser.uid)

        cls.files = cls.c.files
        cls.m = cls.c.downloadManager

    @classmethod
    def tearDownClass(cls):
        cls.db.purgeAll()
        cls.db.shutdown()

    def setUp(self):
        self.test_add_links()

    def test_add_links(self):
        # just generate some links and files
        for user in (adminUser, normalUser):
            for i in range(self.PACKAGES):
                pid = self.files.addPackage("name {:d}", "folder", -1, "", "", "", False, user.uid)
                self.files.addLinks([("url{:d}".format(i), "plugin{:d}".format(i % self.PLUGINS)) for i in range(self.LINKS)], pid, user.uid)

    def test_simple(self):
        jobs = self.db.getJobs([])
        assert len(jobs) == 2

    def test_empty(self):
        assert not self.db.getJobs(["plugin{:d}".format(i) for i in range(self.PLUGINS)])



if __name__ == "__main__":
    TestDownloadManager.benchmark()
