# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals
from builtins import bytes
from builtins import str
from builtins import map

import re

import bitmath
import goslate

from pyload.utils.new.check import isiterable, ismapping


def convert(obj, rule, func, fn_args=(), fn_kwgs={}, fallback=None):
    res = None
    cvargs = (rule, func, fn_args, fn_kwgs, fallback)
    try:
        if rule(obj):
            res = func(obj, *fn_args, **fn_kwgs)
        elif ismapping(obj):
            res = {convert(k, *cvargs): convert(v, *cvargs)
                   for k, v in obj.items()}
        elif isiterable(obj):
            res = type(obj)(convert(i, *cvargs) for i in obj)
        else:
            res = obj
    except Exception as e:
        if callable(fallback):
            return fallback(obj, *cvargs[-1])
        raise
    return res


def accumulate(it, inv_map=None):
    """
    Accumulate (key, value) data to {value : [keylist]} dictionary
    """
    if inv_map is None:
        inv_map = {}
    for key, value in it:
        inv_map.setdefault(value, []).append(key)
    return inv_map


def chunks(iterable, size):
    islice = itertools.islice
    it     = iter(iterable)
    item   = list(islice(it, size))
    while item:
        yield item
        item = list(islice(it, size))


def language(text, target=None, source=None):
    target = target.lower() if target else "en"
    source = source.lower() if source else "auto"

    gs = goslate.Goslate()

    languages = gs.get_languages()
    if target not in languages:
        reverse = {value.lower(): key for key, value in languages.items()}
        target  = reverse.get(target)

    return gs.translate(text, target, source)


def merge(d1, d2):
    """
    Recursively merges d2 into d1
    """
    for key in d2:
        if key in d1 and isinstance(d1, dict) and isinstance(d2, dict):
            d1[key] = merge(d1[key], d2[key])
        else:
            d1[key] = d2[key]
    return d1


def size(value, in_unit, out_unit):
    """
    Convert file size
    """
    in_unit  = in_unit.strip()[0].upper()
    out_unit = out_unit.strip()[0].upper()

    if in_unit == out_unit:
        return value

    # sizeunits = ('B', 'K', 'M', 'G', 'T', 'P', 'E')
    # sizemap   = {u: i * 10 for i, u in enumerate(sizeunits)}

    # in_magnitude  = sizemap[in_unit]
    # out_magnitude = sizemap[out_unit]

    # magnitude = in_magnitude - out_magnitude
    # i, d = divmod(value, 1)

    # decimal = int(d * (1024 ** (abs(magnitude) // 10)))
    # if magnitude >= 0:
        # integer = int(i) << magnitude
    # else:
        # integer = int(i) >> magnitude * -1
        # decimal = -decimal

    # return integer + decimal

    in_unit  += "yte" if in_unit == 'B' else "iB"
    out_unit += "yte" if out_unit == 'B' else "iB"

    in_size  = getattr(bitmath, in_unit)
    out_size = getattr(in_size, 'to_' + out_unit)()
    return out_size.value


def to_bool(value, default=None):
    """
    Convert value to boolean or return default
    """
    try:
        return bool(value)
    except Exception:
        return default


def to_bytes(value, default=None):
    """
    Convert value to bytes or return default
    """
    try:
        try:
            return value.encode('utf-8')
        except Exception:
            return bytes(value)
    except Exception:
        return default


def to_dict(obj, default=None):
    """
    Convert object to dictionary or return default
    """
    try:
        return {attr: getattr(obj, att) for attr in obj.__slots__}
    except Exception:
        return default


def to_float(value, default=None):
    """
    Convert value to fractional or return default
    """
    try:
        return float(value)
    except Exception:
        return default


def to_int(value, default=None):
    """
    Convert value to integer or return default
    """
    try:
        return int(value)
    except Exception:
        return default


def to_list(value, default=None):
    """
    Convert value to a list with value inside or return default
    """
    res = default
    if isinstance(value, list):
        res = value
    elif ismapping(value):
        res = list(value.items())
    elif isiterable(value):
        res = list(value)
    elif value is not None:
        res = [value]
    return res


def to_str(value, default=None):
    """
    Convert value to unicode or return default
    """
    try:
        try:
            return value.decode('utf-8')
        except Exception:
            return str(value)
    except Exception:
        return default


def ver_to_tuple(value, default=None):
    """
    Convert version like string to a tuple of integers or return default
    """
    try:
        values = map(to_int, re.split(r'([\d.,]+)', value))
        return tuple(filter(None, values))
    except Exception:
        return default
