# -*- coding: utf-8 -*-

from tests.helper.Stubs import Core, normalUser, adminUser
from tests.helper.BenchmarkTest import BenchmarkTest

from pyload.database import DatabaseBackend
# disable asyncronous queries
DatabaseBackend.async = DatabaseBackend.queue

class TestDownloadManager(BenchmarkTest):

    bench = ["add_links", "db"]

    @classmethod
    def setUpClass(cls):
        cls.c = Core()
        cls.db = cls.c.db
        cls.db.purgeAll()

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
        for i in range(10):
            pid = self.files.addPackage("name %d", "folder", -1, "", "", "", False, normalUser.uid)
            self.files.addLinks([("plugin%d" % i, "url%d" %i) for i in range(50)], pid, normalUser.uid)

    def test_db(self):
        pass


if __name__ == "__main__":
    TestDownloadManager.benchmark()