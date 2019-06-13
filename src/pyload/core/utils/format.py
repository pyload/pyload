# -*- coding: utf-8 -*-
# AUTHOR: vuolter

import datetime
import os

from .check import isiterable
from .convert import BYTE_PREFIXES, to_str
from .fs import fullpath
from .misc import is_plural

try:
    import bitmath
except ImportError:
    bitmath = None


def attributes(obj, ignore=None):
    if ignore is None:
        attrs = tuple(map(to_str, obj))
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        attrs = (to_str(x) for x in obj if x not in ignored)
    return attrs


def items(obj, ignore=None):
    if ignore is None:
        res = (f"{k}={v}" for k, v in obj.items())
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        res = (f"{k}={v}" for k, v in obj.items() if k not in ignored)
    return res


def path(*paths):
    return os.path.normcase(fullpath(os.path.join(*paths)))


path.from_iterable = lambda it: path(*it)


def size(obj):
    """
    formats size of bytes
    """
    value = float(obj)
    try:
        return bitmath.Byte(value).best_prefix()
    except AttributeError:
        for prefix in BYTE_PREFIXES[:-1]:
            if abs(value) < 1 << 10:
                return f"{value:3.2f} {prefix}"
            else:
                value >>= 10
        return f"{value:.2f} {BYTE_PREFIXES[-1]}"


def speed(obj):
    return f"{size(obj)}/s"


def time(obj):
    seconds = abs(int(obj))
    dt = datetime.datetime(1, 1, 1) + timedelta(seconds=seconds)
    days = dt.day - 1 if dt.day > 1 else 0

    timelist = []

    if days:
        timelist.append(f"{days} day" + ("s" if is_plural(days) else ""))

    timenames = ("hour", "minute", "second")
    for name in timenames:
        value = getattr(dt, name)
        if not value:
            continue
        timelist.append(f"{value} {name}" + ("s" if is_plural(value) else ""))

    return ", ".join(timelist)
