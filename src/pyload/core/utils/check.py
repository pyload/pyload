# -*- coding: utf-8 -*-

import importlib.util
from collections.abc import Iterable, Mapping, Sequence


def is_bits_set(value, bits):
    """Checks if all bits are set in value or some bits are zero."""
    return bits == (value & bits)


def cmp(x, y):
    """Compare the two objects x and y and return an integer according to the
    outcome."""
    return (x > y) - (x < y)


def has_method(obj, name):
    """Check if method `name` was defined in obj."""
    return callable(getattr(obj, name, None))


def has_propriety(obj, name):
    """Check if propriety `name` was defined in obj."""
    attr = getattr(obj, name, None)
    return attr and not callable(attr)


def methods(obj):
    """List all the methods declared in obj."""
    return [name for name in dir(obj) if has_method(obj, name)]


def proprieties(obj):
    """List all the propriety attribute declared in obj."""
    return [name for name in dir(obj) if has_propriety(obj, name)]


def is_iterable(obj, strict=False):
    """Check if object is iterable (`<type 'str'>` excluded if
    strict=False)."""
    return isinstance(obj, Iterable) and (
        strict or not isinstance(obj, str) or not isinstance(obj, bytes)
    )


def is_sequence(obj):
    """Check if object is sequence."""
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray))


def is_mapping(obj):
    """Check if object is mapping."""
    return isinstance(obj, Mapping)


def is_module(name):
    """Check if exists a module with given name."""
    return importlib.util.find_spec(name) is not None


def missing(iterable, start=None, end=None):
    """List all the values between 'start' and 'stop' that are missing from 'iterable'."""
    iter_seq = set(map(int, iterable))
    min_val = start or min(iter_seq)
    max_val = end or max(iter_seq)
    full_seq = set(range(min_val, max_val + 1))
    return sorted(full_seq - iter_seq)
