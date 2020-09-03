# -*- coding: utf-8 -*-

import datetime
import os

import bitmath

from .check import is_iterable
from .convert import BYTE_PREFIXES, to_str
from .fs import fullpath
from .misc import is_plural


def attributes(obj, ignore=None):
    if ignore is None:
        attrs = tuple(map(to_str, obj))
    else:
        ignored = ignore if is_iterable(ignore) else (ignore,)
        attrs = (to_str(x) for x in obj if x not in ignored)
    return attrs


def items(obj, ignore=None):
    if ignore is None:
        res = (f"{k}={v}" for k, v in obj.items())
    else:
        ignored = ignore if is_iterable(ignore) else (ignore,)
        res = (f"{k}={v}" for k, v in obj.items() if k not in ignored)
    return res


def path(*paths):
    return os.path.normcase(fullpath(os.path.join(*paths)))


path.from_iterable = lambda it: path(*it)


def size(value):
    """
    formats size of bytes
    """
    return bitmath.Byte(value).best_prefix().format("{value:.2f} {unit}")


def speed(obj):
    return f"{size(obj)}/s"


def time(obj, literally=True):
    if literally:
        seconds = abs(int(obj))
        dt = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=seconds)
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

    else:
        seconds = int(obj)
        if seconds < 0:
            return "00:00:00"

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
