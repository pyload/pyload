# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import str
from builtins import object
import inspect

# Provide gettext marker
_ = lambda x: x


def find_module(name):
    from imp import find_module

    try:
        f, pathname, desc = find_module(name)
        if f is not None:
            f.close()
        return True
    except Exception:
        return False


class Dependency(object):
    name = None
    optional = True
    desc = None

    @classmethod
    def check(cls):
        """  Returns (availability, version) as tuple """
        inst = cls()
        avail = inst.isStatisfied()
        v = None
        if avail:
            v = inst.getVersion()

        return avail, v

    def is_statisfied(self):
        raise NotImplementedError

    def get_version(self):
        return None


class Python(Dependency):
    name = "Python"
    optional = False

    def is_statisfied(self):
        # obviously
        return True

    def get_version(self):
        import sys

        return ".".join(str(v) for v in sys.version_info[:3])


class JSON(Dependency):
    name = "json"
    optional = False

    def is_statisfied(self):
        return find_module("json") or find_module("simplejson")


class PyCurl(Dependency):
    name = "pycurl"
    optional = False

    def is_statisfied(self):
        return find_module("pycurl")


class Sqlite(Dependency):
    name = "sqlite"
    optional = False

    def is_statisfied(self):
        return find_module("sqlite3") or find_module("pysqlite2")

# TODO: ssl, crypto, image, tesseract, js

deps = [Python, Sqlite, PyCurl, JSON]
