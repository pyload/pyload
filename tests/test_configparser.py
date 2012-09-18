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
        cls.config = ConfigParser()
        cls.db.setup()
        cls.db.clearAllConfigs()


    def test_db(self):

        self.db.saveConfig("plugin", "some value", 0)
        self.db.saveConfig("plugin", "some other value", 1)

        assert self.db.loadConfig("plugin", 0) == "some value"
        assert self.db.loadConfig("plugin", 1) == "some other value"

        d = self.db.loadAllConfigs()
        assert d[0]["plugin"] == "some value"

        self.db.deleteConfig("plugin")

        assert not self.db.loadAllConfigs()


    def test_dict(self):

        assert self.config["general"]["language"]
        self.config["general"]["language"] = "de"
        assert self.config["general"]["language"] == "de"

    def test_config(self):
        pass

    def test_userconfig(self):
        pass