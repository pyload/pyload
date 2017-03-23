# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import datetime
import os
import re
import sys
import urllib.parse
from builtins import int, map, str

from future import standard_library
standard_library.install_aliases()

from pyload.utils import purge

from .check import isiterable
from .decorator import iterate

try:
    import bitmath
except ImportError:
    pass


__all__ = [
    'attributes',
    'items',
    'name',
    'path',
    'size',
    'speed',
    'time',
    'url']


def attributes(obj, ignore=None):
    if ignore is None:
        return list(map(str, obj))
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        return [str(x) for x in obj if x not in ignored]


def items(obj, ignore=None):
    if ignore is None:
        return ["{0}={1}".format(k, v) for k, v in obj.items()]
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        return ["{0}={1}".format(k, v)
                for k, v in obj.items() if k not in ignored]


@iterate
def name(s, sep='_'):
    """
    Remove invalid characters.
    """
    unixbadchars = ('\0', '/', '\\')
    macbadchars = ('\0', ':', '/', '\\')
    winbadchars = ('\0', '<', '>', ':', '"', '/', '\\', '|', '?', '*')
    winbadwords = ('com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8',
                   'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7',
                   'lpt8', 'lpt9', 'con', 'prn')

    repl = ' '
    if os.name == 'nt':
        repl += r''.join(winbadchars)
    elif sys.platform == 'darwin':
        repl += r''.join(macbadchars)
    else:
        repl += r''.join(unixbadchars)

    name = purge.chars(s.strip(), repl, sep).strip()

    if os.name == 'nt' and name in winbadwords:
        name = '_' + name

    return name


def path(*paths):
    """
    Remove invalid characters and truncate the path if needed.
    """
    path = os.path.join(*paths)

    drive, filename = os.path.splitdrive(path)

    nameparts = [name(chunk) for chunk in filename.split(os.sep)]
    dirname = os.path.join(*nameparts[:-1]) + os.sep

    root, ext = os.path.splitext(nameparts[-1])
    root = root.rstrip('.')
    ext = ext.lstrip('_')
    basename = root + ext

    sep = os.sep if os.path.isabs(path) else ""
    if sep:
        pathlen = len(drive + sep + dirname)
        namelen = 255 if os.name == 'nt' else 1024 if sys.platform == 'darwin' else 4096
        maxlen = namelen - pathlen
    else:
        maxlen = 255

    overflow = len(basename) - maxlen
    if overflow > 0:
        root = purge.truncate(root, overflow)
        basename = root + ext

    path = os.path.normcase(drive + sep + dirname + basename)
    return path


@iterate
def size(s):
    try:
        return bitmath.Byte(s).best_prefix()
    except NameError:
        for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB'):
            if abs(s) < 1024.0:
                return "{0:3.2f} {1}".format(s, unit)
            else:
                s /= 1024.0
        return "{0:.2f} {1}".format(s, 'YiB')


@iterate
def speed(s):
    return size(s) + "/s"


@iterate
def time(s):
    sec = abs(int(s))
    dt = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=sec)
    days = dt.day - 1 if dt.day else 0

    attrlist = ("hour", "minute", "second")
    timelist = ["{0:d} {1}s".format(getattr(dt, attr), attr)
                for attr in attrlist if getattr(dt, attr)]
    timemsg = ", ".join(timelist)

    return "{0} days and {1}".format(days, timemsg) if days else timemsg


_re_url = re.compile(r'(?<!:)/{2,}')


@iterate
def url(url):
    from .web import purge as webpurge
    url = urllib.parse.unquote(url.decode('unicode-escape'))
    url = webpurge.text(url).lstrip('.').lower()
    url = _re_url.sub('/', url).rstrip('/')
    return url
