# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import range
from random import choice
from unittest import TestCase

from pyload.core import Core
from tests.api.apitester import ApiTester


class TestAPI(TestCase):
    """
    Test all available testers randomly and on all backends.
    """
    _multiprocess_can_split_ = True
    core = None

    # TODO: parallel testing
    @classmethod
    def setUpClass(cls):
        from tests.api.test_noargs import TestNoArgs

        cls.core = Core()
        cls.core.start(False, False, True)
        for Test in (TestNoArgs,):
            t = Test()
            t.enable_json()
            t = Test()
            t.enable_ws()
            t = Test()
            t.set_api(cls.core.api)

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
