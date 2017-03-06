# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

import os

from future import standard_library

# needed to register globals
from tests.helper import stubs
from unittest2 import TestCase

standard_library.install_aliases()


PACKDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSyntax(TestCase):
    pass


for dir, dirnames, filenames in os.walk(os.path.join(PACKDIR, "pyload")):
    for filename in filenames:
        if not filename.endswith(".py") or filename.startswith("__"):
            continue
        file = os.path.join(PACKDIR, filename)
        pack = file.replace(PACKDIR, "")[1:-3]  #: replace / and  .py
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
        sig = "test_{}_{}".format(packages[-2], packages[-1])
        setattr(TestSyntax, sig, meta(imp, sig))
