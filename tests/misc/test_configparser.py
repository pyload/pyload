# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library

from nose.tools import raises
from tests.helper.stubs import Core

standard_library.install_aliases()


class TestConfig(object):

    @classmethod
    def setUpClass(cls):
        # Only needed to get imports right
        cls.core = Core()
        cls.config = cls.core.config

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
