# -*- coding: utf-8 -*-

import imp
from collections.abc import Iterable, Mapping


def bitset(bits, bset):
    """Checks if all bits are set in bset or bits is zero."""
    return bits == (bits & bset)


def cmp(x, y):
    """Compare the two objects x and y and return an integer according to the
    outcome."""
    return (x > y) - (x < y)


def hasmethod(obj, name):
    """Check if method `name` was defined in obj."""
    return callable(getattr(obj, name, None))


def haspropriety(obj, name):
    """Check if propriety `name` was defined in obj."""
    attr = getattr(obj, name, None)
    return attr and not callable(attr)


def methods(obj):
    """List all the methods declared in obj."""
    return [name for name in dir(obj) if hasmethod(obj, name)]


def proprieties(obj):
    """List all the propriety attribute declared in obj."""
    return [name for name in dir(obj) if haspropriety(obj, name)]


def is_iterable(obj, strict=False):
    """Check if object is iterable (`<type 'str'>` excluded if
    strict=False)."""
    return isinstance(obj, Iterable) and (
        strict or not isinstance(obj, str) or not isinstance(obj, bytes)
    )


def is_mapping(obj):
    """Check if object is mapping."""
    return isinstance(obj, Mapping)


def is_module(name, path=None):
    """Check if exists a module with given name."""
    try:
        fp, _, _ = imp.find_module(name, path)
        if fp is not None:
            fp.close()
        return True
    except ImportError:
        return False


def missing(iterable, start=None, end=None):
    iter_seq = set(map(int, iterable))
    min_val = start or min(iter_seq)
    max_val = end or max(iter_seq)
    full_seq = set(range(min_val, max_val + 1))
    return sorted(full_seq - iter_seq)
