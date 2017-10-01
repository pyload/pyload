# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from builtins import bytes, dict, int, str

from future import standard_library

from .check import isiterable, ismapping

standard_library.install_aliases()


try:
    import bitmath
except ImportError:
    bitmath = None


def convert(obj, rule, func, args=(), kwargs={}, fallback=None):
    res = None
    cvargs = (rule, func, args, kwargs, fallback)
    try:
        if rule(obj):
            res = func(obj, *args, **kwargs)
        elif ismapping(obj):
            res = dict((convert(k, *cvargs), convert(v, *cvargs))
                       for k, v in obj.items())
        elif isiterable(obj):
            res = type(obj)(convert(i, *cvargs) for i in obj)
        else:
            res = obj
    except Exception as e:
        if callable(fallback):
            fbargs = cvargs[:-1] + (e,)
            return fallback(obj, *fbargs)
        raise
    return res


def size(value, in_unit, out_unit):
    """Convert file size."""
    in_unit = in_unit.strip()[0].upper()
    out_unit = out_unit.strip()[0].upper()

    if in_unit == out_unit:
        return value

    in_unit += 'yte' if in_unit == 'B' else 'iB'
    out_unit += 'yte' if out_unit == 'B' else 'iB'

    try:
        # Create a bitmath instance representing the input value with its
        # corresponding unit
        in_size = getattr(bitmath, in_unit)(value)
        # Call the instance method to convert it to the output unit
        out_size = getattr(in_size, 'to_' + out_unit)()
        return out_size.value

    except AttributeError:
        sizeunits = ('B', 'K', 'M', 'G', 'T', 'P', 'E')
        sizemap = dict((u, i * 10) for i, u in enumerate(sizeunits))

        in_magnitude = sizemap[in_unit]
        out_magnitude = sizemap[out_unit]

        magnitude = in_magnitude - out_magnitude
        i, d = divmod(value, 1)

        decimal = int(d * (1024 ** (abs(magnitude) // 10)))
        if magnitude >= 0:
            integer = int(i) << magnitude
        else:
            integer = int(i) >> magnitude * -1
            decimal = -decimal

        return integer + decimal


def to_bool(value, default=None, exc=Exception):
    """Convert value to boolean or return default."""
    try:
        return bool(value)
    except exc:
        return default


def to_bytes(value, default=None, exc=Exception):
    """Convert value to bytes or return default."""
    try:
        try:
            return value.encode('utf-8')
        except Exception:
            return bytes(value)
    except exc:
        return default


def to_dict(obj, default=None, exc=Exception):
    """Convert object to dictionary or return default."""
    try:
        return dict((attr, getattr(obj, attr)) for attr in obj.__slots__)
    except exc:
        return default


def to_float(value, default=None, exc=Exception):
    """Convert value to fractional or return default."""
    try:
        return float(value)
    except exc:
        return default


def to_int(value, default=None, exc=Exception):
    """Convert value to integer or return default."""
    try:
        return int(value)
    except exc:
        return default


def to_list(value, default=None, exc=Exception):
    """Convert value to a list with value inside or return default."""
    try:
        if isinstance(value, list):
            res = value
        elif ismapping(value):
            res = list(value.items())
        elif isiterable(value, strict=False):
            res = list(value)
        elif value is not None:
            res = [value]
        else:
            res = list(value)
    except exc:
        return default
    return res


def to_str(value, default=None, exc=Exception):
    """Convert value to unicode or return default."""
    try:
        try:
            return value.decode('utf-8')
        except Exception:
            return str(value)
    except exc:
        return default
