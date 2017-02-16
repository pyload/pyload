# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from __future__ import print_function
from __future__ import division

from future import standard_library
standard_library.install_aliases()
import inspect

from pyload.remote.apitypes import Iface
from tests.api.apitester import ApiTester

IGNORE = ('quit', 'restart')


class TestNoArgs(ApiTester):

    def setUp(self):
        self.enable_json()

# Setup test_methods dynamically, only these which require no arguments
for name in dir(Iface):
    if name.startswith("_") or name in IGNORE:
        continue

    spec = inspect.getargspec(getattr(Iface, name))
    if len(spec.args) == 1 and (not spec.varargs or len(spec.varargs) == 0):
        def meta_test(name):  #: retain local scope
            def test(self):
                getattr(self.api, name)()
            test.__name__ = "test_{}".format(name)
            return test

        setattr(TestNoArgs, "test_{}".format(name), meta_test(name))

        del meta_test
