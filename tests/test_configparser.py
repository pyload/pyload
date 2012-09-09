# -*- coding: utf-8 -*-

from collections import defaultdict
from helper.Stubs import Core

from module.database import DatabaseBackend
from module.config.ConfigParser import ConfigParser

# TODO
class TestConfigParser():

    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseBackend(Core())
        cls.db.manager = cls.db.core
        cls.db.manager.statusMsg = defaultdict(lambda: "statusmsg")
        cls.config = ConfigParser


    def test_db(self):
        pass

    def test_dict(self):
        pass

    def test_config(self):
        pass

    def test_userconfig(self):
        pass