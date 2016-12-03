# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import object
from tests.helper.Stubs import Core


class TestStatDatabase(object):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        cls.db = cls.core.db

    def test_simple(self):
        assert 1 == 0
