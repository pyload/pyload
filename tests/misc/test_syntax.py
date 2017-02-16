# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
import os

# needed to register globals
from tests.helper import stubs
from unittest2 import TestCase

PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        "..",
        "..",
        ""))


class TestSyntax(TestCase):
    pass


for path, dirs, files in os.walk(os.path.join(PATH, "pyload")):

    for f in files:
        if not f.endswith(".py") or f.startswith("__"):
            continue
        fpath = os.path.join(path, f)
        pack = fpath.replace(PATH, "")[1:-3]  #: replace / and  .py
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
