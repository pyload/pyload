# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import range
from unittest import TestCase
from random import choice

from pyload.Core import Core

from .ApiTester import ApiTester


class TestAPI(TestCase):
    """
    Test all available testers randomly and on all backends
    """
    _multiprocess_can_split_ = True
    core = None

    #TODO: parallel testing
    @classmethod
    def setUpClass(cls):
        from .test_noargs import TestNoArgs

        cls.core = Core()
        cls.core.start(False, False, True)
        for Test in (TestNoArgs,):
            t = Test()
            t.enableJSON()
            t = Test()
            t.enableWS()
            t = Test()
            t.setApi(cls.core.api)

        cls.methods = ApiTester.get_methods()

    @classmethod
    def tearDownClass(cls):
        cls.core.shutdown()

    def test_random(self, n=10000):
        for i in range(n):
            func = choice(self.methods)
            func()

    def test_random2(self, n):
        self.test_random(n)

    def test_random3(self, n):
        self.test_random(n)

    def test_random4(self, n):
        self.test_random(n)
