# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from past.builtins import basestring
from builtins import object
from nose.tools import raises

from tests.helper.stubs import Core

from pyload.config.configparser import ConfigParser


class TestConfigParser(object):

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

    def test_iter(self):
        for section, config, values in self.config.iterSections():
            assert isinstance(section, basestring)
            assert isinstance(config.config, dict)
            assert isinstance(values, dict)

    def test_get(self):
        assert self.config.getSection("general")[0].config

    @raises(KeyError)
    def test_invalid_config(self):
        print(self.config["invalid"]["config"])

    @raises(KeyError)
    def test_invalid_section(self):
        print(self.config["general"]["invalid"])
