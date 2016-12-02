# -*- coding: utf-8 -*-

import inspect

from ApiTester import ApiTester

from pyload.remote.apitypes import Iface

IGNORE = ('quit', 'restart')

class TestNoArgs(ApiTester):
    def setUp(self):
        self.enableJSON()

# Setup test_methods dynamically, only these which require no arguments
for name in dir(Iface):
    if name.startswith("_") or name in IGNORE: continue

    spec = inspect.getargspec(getattr(Iface, name))
    if len(spec.args) == 1 and (not spec.varargs or len(spec.varargs) == 0):
        def meta_test(name): #retain local scope
            def test(self):
                getattr(self.api, name)()
            test.func_name = "test_%s" % name
            return test

        setattr(TestNoArgs, "test_%s" % name, meta_test(name))

        del meta_test
