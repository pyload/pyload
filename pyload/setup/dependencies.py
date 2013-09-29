# -*- coding: utf-8 -*-

# Provide gettext marker
_ = lambda x: x


def find_module(name):
    from imp import find_module

    try:
        f, pathname, desc = find_module(name)
        if f is not None:
            f.close()
        return True
    except:
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

    def isStatisfied(self):
        raise NotImplementedError

    def getVersion(self):
        return None


class Python(Dependency):
    name = "Python"
    optional = False

    def isStatisfied(self):
        # obviously
        return True

    def getVersion(self):
        import sys

        ".".join(str(v) for v in sys.version_info[:3])


class JSON(Dependency):
    name = "json"
    optional = False

    def isStatisfied(self):
        # TODO
        return True


class PyCurl(Dependency):
    name = "pycurl"
    optional = False

    def isStatisfied(self):
        # TODO
        return True


class Sqlite(Dependency):
    name = "sqlite"
    optional = False

    def isStatisfied(self):
        # TODO
        return True

# TODO: ssl, crypto, image, tesseract, js

deps = [x for x in locals().itervalues() if issubclass(x, Dependency) and x is not Dependency]