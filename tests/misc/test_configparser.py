# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import object, str

from nose.tools import raises
from pyload.config import Config
from tests.helper.stubs import Core


class TestConfig(object):

    @classmethod
    def setUpClass(cls):
        # Only needed to get imports right
        cls.core = Core()
        cls.config = Config()

    def test_dict(self):

        assert self.config.get('general', 'language')
        self.config.set('general', 'language', 'en')
        assert self.config.get('general', 'language') == "en"

    def test_contains(self):

        assert "general" in self.config
        assert "foobaar" not in self.config

    def test_iter(self):
        for section, config, values in self.config.iter_sections():
            assert isinstance(section, str)
            assert isinstance(config.config, dict)
            assert isinstance(values, dict)

    def test_get(self):
        assert self.config.get_section("general")[0].config

    @raises(KeyError)
    def test_invalid_config(self):
        print(self.config.get('invalid', 'config'))

    @raises(KeyError)
    def test_invalid_section(self):
        print(self.config.get('general', 'invalid'))
