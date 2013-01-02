# -*- coding: utf-8 -*-

from nose.tools import raises

from tests.helper.Stubs import Core

from module.config.ConfigParser import ConfigParser

class TestConfigParser():

    @classmethod
    def setUpClass(cls):
        # Only needed to get imports right
        cls.core = Core()
        cls.config = ConfigParser()

    def test_dict(self):

        assert self.config["general"]["language"]
        self.config["general"]["language"] = "de"
        assert self.config["general"]["language"] == "de"

    def test_contains(self):

        assert "general" in self.config
        assert "foobaar" not in self.config


    @raises(KeyError)
    def test_invalid_config(self):
        print self.config["invalid"]["config"]

    @raises(KeyError)
    def test_invalid_section(self):
        print self.config["general"]["invalid"]