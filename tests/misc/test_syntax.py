# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from os import walk
from os.path import abspath, dirname, join
from unittest2 import TestCase

# needed to register globals
from tests.helper import stubs

PATH = abspath(join(dirname(abspath(__file__)), "..", "..", ""))


class TestSyntax(TestCase):
    pass


for path, dirs, files in walk(join(PATH, "pyload")):

    for f in files:
        if not f.endswith(".py") or f.startswith("__"):
            continue
        fpath = join(path, f)
        pack = fpath.replace(PATH, "")[1:-3]  # replace / and  .py
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
