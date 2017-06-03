# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library

from tests.helper.stubs import Core

standard_library.install_aliases()


class TestStatDatabase(object):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    def test_simple(self):
        assert 1 == 0
