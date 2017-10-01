# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import datetime
import os
from builtins import int, str

from future import standard_library

from pyload.utils.check import isiterable
from pyload.utils.fs import fullpath

standard_library.install_aliases()


try:
    import bitmath
except ImportError:
    bitmath = None


def attributes(obj, ignore=None):
    if ignore is None:
        attrs = (str(x) for x in obj)
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        attrs = (str(x) for x in obj if x not in ignored)
    return attrs


def items(obj, ignore=None):
    if ignore is None:
        res = ('{0}={1}'.format(k, v) for k, v in obj.items())
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        res = ('{0}={1}'.format(k, v) for k, v in obj.items()
               if k not in ignored)
    return res


def path(*paths):
    return os.path.normcase(fullpath(os.path.join(*paths)))


__byte_prefixes = ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi')


def size(obj):
    KIB = 1024.0
    num = float(obj)
    try:
        return bitmath.Byte(num).best_prefix()
    except AttributeError:
        for prefix in __byte_prefixes[:-1]:
            if abs(num) < KIB:
                return '{0:3.2f} {1}B'.format(num, prefix)
            else:
                num /= KIB
        return '{0:.2f} {1}B'.format(num, __byte_prefixes[-1])


def speed(obj):
    return '{0}/s'.format(size(obj))


def time(obj):
    sec = abs(int(obj))
    dt = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=sec)
    days = dt.day - 1 if dt.day else 0
    attrlist = ('hour', 'minute', 'second')
    timelist = (
        '{0:d} {1}s'.format(getattr(dt, attr), attr)
        for attr in attrlist if getattr(dt, attr))
    if days:
        timelist.append('{0:d} days'.format(days))
    return timelist
