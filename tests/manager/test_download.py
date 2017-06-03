#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import range

from future import standard_library

from pyload.core.database import DatabaseBackend
from tests.helper.benchmark import BenchmarkTest
from tests.helper.stubs import Core, admin_user, normal_user, other_user

standard_library.install_aliases()


# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue


class TestTransferManager(BenchmarkTest):

    bench = ["add_links", "simple", "empty"]

    USER = 2
    PACKAGES = 10
    LINKS = 50
    PLUGINS = 10

    @classmethod
    def setUpClass(cls):
        cls.c = Core()
        cls.db = cls.c.db
        cls.db.purge_all()
        cls.db.add_debug_user(normal_user.uid)
        cls.db.add_debug_user(admin_user.uid)
        cls.db.add_debug_user(other_user.uid)

        cls.files = cls.c.files
        cls.m = cls.c.tfm

    @classmethod
    def tearDownClass(cls):
        cls.db.purge_all()
        cls.db.shutdown()

    def setUp(self):
        self.test_add_links()

    def test_add_links(self):
        # just generate some links and files
        for user in (admin_user, normal_user):
            for i in range(self.PACKAGES):
                pid = self.files.add_package(
                    "name {0:d}", "folder", -1, "", "", "", False, user.uid)
                self.files.add_links(
                    (("url{0:d}".format(i),
                      "plugin{0:d}".format(i % self.PLUGINS))
                     for i in range(self.LINKS)),
                    pid, user.uid)

    def test_simple(self):
        jobs = self.db.get_jobs([])
        assert len(jobs) == 2

    def test_empty(self):
        assert not self.db.get_jobs(
            "plugin{0:d}".format(i) for i in range(self.PLUGINS))


if __name__ == '__main__':
    TestTransferManager.benchmark()
