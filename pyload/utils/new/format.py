# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import map

import datetime
import urllib.parse

import bitmath

from pyload.utils.new import purge, web as webutils
from pyload.utils.new.check import isiterable
from pyload.utils.new.decorator import iterable


def iter(obj, ignore=None):
    if ignore is None:
        return map(str, obj)
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        return [str(x) for x in obj if x not in ignored]


def map(obj, ignore=None):
    if ignore is None:
        return ["{}={}".format(k, v) for k, v in obj.items()]
    else:
        ignored = ignore if isiterable(ignore) else (ignore,)
        return ["{}={}".format(k, v) for k, v in obj.items() if k not in ignored]


@iterate
def name(value):
    """
    Remove invalid characters.
    """
    unixbadchars = ('\0', '/', '\\')
    winbadchars  = ('\0', '<', '>', '"', '/', '\\', '|', '?', '*')
    winbadwords  = ('com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8',
                    'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7',
                    'lpt8', 'lpt9', 'con', 'prn')

    deletechars = r''.join(winbadchars if os.name == "nt" else unixbadchars)
    if isinstance(value, str):
        name = purge.chars(value, deletechars)
    else:
        name = value.translate(None, deletechars)

    name = re.sub(r'[\s:]+', '_', name).strip('_')

    if os.name == "nt" and name in winbadwords:
        name = '_' + name

    return name


def path(*paths):
    """
    Remove invalid characters and truncate the path if needed.
    """
    value = os.path.join(*paths)

    unt, rest       = os.path.splitunc(value) if os.name == 'nt' else ("", value)
    drive, filename = os.path.splitdrive(rest)

    sep = os.sep if os.path.isabs(filename) else ""
    nameparts = map(name, filename.split(os.sep))

    filename = os.path.join(*nameparts)
    filepath = unt + drive + sep + filename

    try:
        length = len(filepath) - 259  #@NOTE: Max 260 chars fs indipendent
        if length < 1:
            return

        dirname, basename = os.path.split(filename)
        root, ext = os.path.splitext(basename)

        filename = dirname + purge.truncate(root, length) + ext
        filepath = unt + drive + sep + filename

    finally:
        return filepath


@iterate
def size(value):
    # for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'):
        # if abs(value) < 1024.0:
            # return "{:3.2f} {}".format(value, unit)
        # else:
            # value /= 1024.0
    # return "{:.2f} {}".format(value, 'EiB')
    return bitmath.Byte(value).best_prefix()


@iterate
def speed(value):
    return size(value) + "/s"


@iterate
def time(value):
    sec  = abs(int(value))
    dt   = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=sec)
    days = dt.day - 1 if dt.day else 0

    attrlist = ("hour", "minute", "second")
    timelist = ["{:d} {}s".format(getattr(dt, attr), attr) for attr in attrlist if getattr(dt, attr)]
    timemsg  = ", ".join(timelist)

    return "{} days and {}".format(days, timemsg) if days else timemsg


@iterate
def url(url):
    url = urllib.parse.unquote(url.decode('unicode-escape'))
    url = webutils.purge.text(url).lstrip('.').lower()
    url = re.sub(r'(?<!:)/{2,}', '/', url).rstrip('/')
    return url
