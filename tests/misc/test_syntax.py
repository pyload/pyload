# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from future import standard_library

import os

# needed to register globals
from tests.helper import stubs
from unittest2 import TestCase

standard_library.install_aliases()


PACKDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSyntax(TestCase):
    pass


for dir, dirnames, filenames in os.walk(os.path.join(PACKDIR, "pyload")):
    for fname in filenames:
        if not fname.endswith(".py") or fname.startswith("__"):
            continue
        path = os.path.join(PACKDIR, fname)
        pack = path.replace(PACKDIR, "")[1:-3]  #: replace / and  .py
        imp = pack.replace("/", ".")
        packages = imp.split(".")
        #__import__(imp)

        # to much sideeffect when importing
        if "web" in packages or "lib" in packages:
            continue

        # currying
        def meta(imp, sig):
            def _test(self=None):
                __import__(imp)

            _test.__name__ = sig
            return _test

        # generate test methods
        sig = "test_{0}_{1}".format(packages[-2], packages[-1])
        setattr(TestSyntax, sig, meta(imp, sig))
