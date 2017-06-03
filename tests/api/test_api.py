# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import random
from builtins import range

from future import standard_library

from pyload.core import Core
from tests.api.apitester import ApiTester
from unittest2 import TestCase

standard_library.install_aliases()


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
        for Test in (TestNoArgs,):
            test = Test()
            test.enable_json()
            test = Test()
            test.enable_ws()
            test = Test()
            test.set_api(cls.core.api)

        cls.methods = ApiTester.get_methods()

    @classmethod
    def tearDownClass(cls):
        cls.core.shutdown()

    def test_random(self, n=10000):
        for i in range(n):
            func = random.choice(self.methods)
            func()

    def test_random2(self, n):
        self.test_random(n)

    def test_random3(self, n):
        self.test_random(n)

    def test_random4(self, n):
        self.test_random(n)
