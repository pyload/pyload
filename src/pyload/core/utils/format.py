# -*- coding: utf-8 -*-
# AUTHOR: vuolter

from __future__ import absolute_import, unicode_literals

import datetime
import os

from future import standard_library
from future.builtins import int

from pyload.utils.check import isiterable
from pyload.utils.convert import to_str, BYTE_PREFIXES
from pyload.utils.fs import fullpath
from pyload.utils.misc import is_plural

standard_library.install_aliases()


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
        res = ('{0}={1}'.format(k, v) for k, v in obj.items())
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        res = ('{0}={1}'.format(k, v) for k, v in obj.items()
               if k not in ignored)
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
                return '{:3.2f} {}'.format(value, prefix)
            else:
                value >>= 10
        return '{:.2f} {}'.format(value, BYTE_PREFIXES[-1])
    
    
def speed(obj):
    return '{0}/s'.format(size(obj))


def time(obj):
    seconds = abs(int(obj))
    dt = datetime.datetime(1, 1, 1) + timedelta(seconds=seconds)
    days = dt.day - 1 if dt.day > 1 else 0
    
    timelist = []
    
    if days:
        timelist.append('{} day{}'.format(days, "s" if is_plural(days) else ""))
        
    timenames = ('hour', 'minute', 'second')
    for name in timenames:
        value = getattr(dt, name)
        if not value:
            continue
        timelist.append("{} {}{}".format(value, name, "s" if is_plural(value) else "")
        
    return ", ".join(timelist)
