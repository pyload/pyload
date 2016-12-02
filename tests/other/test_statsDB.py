# -*- coding: utf-8 -*-

from tests.helper.Stubs import Core

class TestStatDatabase():

    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        cls.db = cls.core.db

    def test_simple(self):
        assert 1 == 0
