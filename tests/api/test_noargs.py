# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import inspect

from future import standard_library

from pyload.core.api import AbstractApi
from tests.api.apitester import ApiTester

standard_library.install_aliases()


IGNORE = ('quit', 'restart')


class TestNoArgs(ApiTester):

    def setUp(self):
        self.enable_json()


# Setup test_methods dynamically, only these which require no arguments
for name in dir(AbstractApi):
    if name.startswith("_") or name in IGNORE:
        continue

    spec = inspect.getargspec(getattr(AbstractApi, name))
    if len(spec.args) == 1 and (not spec.varargs or len(spec.varargs) == 0):
        def meta_test(name):  # retain local scope
            def test(self):
                getattr(self.api, name)()
            test.__name__ = "test_{0}".format(name)
            return test

        setattr(TestNoArgs, "test_{0}".format(name), meta_test(name))

        del meta_test
