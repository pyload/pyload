# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, division, unicode_literals

import itertools
import re

from builtins import bytes, int, map, str

from future import standard_library
standard_library.install_aliases()

import goslate

from .check import isiterable, ismapping

try:
    import bitmath
except ImportError:
    pass


__all__ = ['accumulate', 'chunks', 'convert', 'from_version', 'language',
           'merge', 'size', 'to_bool', 'to_bytes', 'to_dict', 'to_float',
           'to_int', 'to_list', 'to_str', 'to_version']


def convert(obj, rule, func, fn_args=(), fn_kwgs={}, fallback=None):
    res = None
    cvargs = (rule, func, fn_args, fn_kwgs, fallback)
    try:
        if rule(obj):
            res = func(obj, *fn_args, **fn_kwgs)
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


def accumulate(it, inv_map=None):
    """
    Accumulate (key, value) data to {value : [keylist]} dictionary.
    """
    if inv_map is None:
        inv_map = {}
    for key, value in it:
        inv_map.setdefault(value, []).append(key)
    return inv_map


def chunks(iterable, size):
    islice = itertools.islice
    it = iter(iterable)
    item = list(islice(it, size))
    while item:
        yield item
        item = list(islice(it, size))


def language(text, target=None, source=None):
    target = target.lower() if target else "en"
    source = source.lower() if source else "auto"

    gs = goslate.Goslate()

    languages = gs.get_languages()
    if target not in languages:
        reverse = dict((value.lower(), key) for key, value in languages.items())
        target = reverse.get(target)

    return gs.translate(text, target, source)


def merge(d1, d2):
    """
    Recursively merges d2 into d1.
    """
    for key in d2:
        if key in d1 and isinstance(d1, dict) and isinstance(d2, dict):
            d1[key] = merge(d1[key], d2[key])
        else:
            d1[key] = d2[key]
    return d1


def size(value, in_unit, out_unit):
    """
    Convert file size.
    """
    in_unit = in_unit.strip()[0].upper()
    out_unit = out_unit.strip()[0].upper()

    if in_unit == out_unit:
        return value

    in_unit += "yte" if in_unit == 'B' else "iB"
    out_unit += "yte" if out_unit == 'B' else "iB"

    try:
        in_size = getattr(bitmath, in_unit)
        out_size = getattr(in_size, 'to_' + out_unit)()
        return out_size.value

    except NameError:
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
    """
    Convert value to boolean or return default.
    """
    try:
        return bool(value)
    except exc:
        return default


def to_bytes(value, default=None, exc=Exception):
    """
    Convert value to bytes or return default.
    """
    try:
        try:
            return value.encode('utf-8')
        except Exception:
            return bytes(value)
    except exc:
        return default


def to_dict(obj, default=None, exc=Exception):
    """
    Convert object to dictionary or return default.
    """
    try:
        return dict((attr, getattr(obj, attr)) for attr in obj.__slots__)
    except exc:
        return default


def to_float(value, default=None, exc=Exception):
    """
    Convert value to fractional or return default.
    """
    try:
        return float(value)
    except exc:
        return default


def to_int(value, default=None, exc=Exception):
    """
    Convert value to integer or return default.
    """
    try:
        return int(value)
    except exc:
        return default


def to_list(value, default=None, exc=Exception):
    """
    Convert value to a list with value inside or return default.
    """
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
    """
    Convert value to unicode or return default.
    """
    try:
        try:
            return value.decode('utf-8')
        except Exception:
            return str(value)
    except exc:
        return default


def from_version(value, default=None, exc=Exception):
    """
    Convert version tuple to version like string or return default.
    """
    try:
        return '.'.join(to_str(num, num) for num in value)
    except exc:
        return default


_re_vtt = re.compile(r'\D+')

def to_version(value, default=None, exc=Exception):
    """
    Convert version like string to a version tuple of integers or return default.
    """
    try:
        return tuple(int(_f) for _f in _re_vtt.split(value) if _f)
    except exc:
        return default
