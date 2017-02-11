# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

import imp
import os
import sys
from builtins import map, range

from pyload.utils.lib.collections import Iterable, Mapping


def bitset(bits, compare):
    """
    Checks if all bits are set in compare, or bits is 0.
    """
    return bits == (bits & compare)


def hasmethod(obj, name):
    """
    Check if method `name` was defined in obj.
    """
    return callable(getattr(obj, name, None))


def haspropriety(obj, name):
    """
    Check if propriety `name` was defined in obj.
    """
    attr = getattr(obj, name, None)
    return attr and not callable(attr)


def methods(obj):
    """
    List all the methods declared in obj.
    """
    return [name for name in dir(obj) if hasmethod(obj, name)]


def proprieties(obj):
    """
    List all the propriety attribute declared in obj.
    """
    return [name for name in dir(obj) if haspropriety(obj, name)]


def isiterable(obj, strict=False):
    """
    Check if object is iterable (`<type 'str'>` excluded if strict=False).
    """
    return (isinstance(obj, Iterable)
            and (strict or not isinstance(obj, str)))


def ismapping(obj):
    """
    Check if object is mapping.
    """
    return isinstance(obj, Mapping)


def ismodule(name, path=None):
    """
    Check if exists a module with given name.
    """
    try:
        f, filename, desc = imp.find_module(name, path)
        if f is not None:
            f.close()
        return True
    except ImportError:
        return False


# TODO: Recheck in 0.5.x
def lookup(enc=None):
    if os.name != 'nt':
        return 'utf-8'
    if not enc:
        enc = sys.stdout.encoding
    return "cp850" if enc == "cp65001" else enc  #: aka UTF-8 under Windows


def missingitems(iterable, start=None, end=None):
    iter_seq = set(map(int, iterable))
    min_val = start or min(iter_seq)
    max_val = end or max(iter_seq)
    full_seq = set(range(min_val, max_val + 1))
    return sorted(full_seq - iter_seq)
