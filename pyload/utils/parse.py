# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, division, unicode_literals

import os
import re
from builtins import dict

from future import standard_library

import mimetypes
from pyload.utils import convert, format, purge

from .decorator import iterate
from .layer.legacy import hashlib_ as hashlib
from .time import to_midnight

standard_library.install_aliases()


__all__ = [
    'alias',
    'boolean',
    'entries',
    'hash',
    'mime',
    'name',
    'number',
    'packs',
    'size',
    'time']


_re_alias = re.compile(r'[\d.-_]+')


@iterate
def alias(value):
    chunks = _re_alias.split(format.name(value))
    return ''.join(word.capitalize() for word in chunks if word)


_re_boolean = re.compile(r'1|y|true', flags=re.I)


@iterate
@purge.args
def boolean(value):
    return _re_boolean.match(value) is not None


_re_entries = re.compile(r'[;,\s]+')


@iterate
def entries(value):
    return [entry for entry in _re_entries.sub('|', value).split('|') if entry]


@iterate
@purge.args
def hash(value):
    value = value.replace('-', '').lower()
    algop = '|'.join(hashlib.algorithms + ('adler32', 'crc(32)?'))
    pattr = r'(?P<D1>{}|)\s*[:=]?\s*(?P<H>[\w^_]{8,}?)\s*[:=]?\s*(?P<D2>{}|)'
    pattr = pattr.format(algop, algop)
    m = re.search(pattr, value)
    if not m:
        return None, None

    checksum = m.group('H')
    algorithm = m.group('D1') or m.group('D2')
    if algorithm == 'crc':
        algorithm = "crc32"

    return checksum, algorithm


# TODO: Recheck in 0.5.x
@iterate
@purge.args
def name(value):
    from .web import check as webcheck
    if webcheck.isurl(value):
        from .web import convert as webconvert
        return webconvert.url_to_name(value)
    else:
        return os.path.basename(value)


@iterate
@purge.args
def mime(value):
    return mimetypes.guess_type(name, strict=False)[0]


_re_number = re.compile(r'[\s-]+')


@iterate
@purge.args
def number(value):
    value = value.lower()
    ones = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen")
    tens = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty",
            "ninety")

    o_tuple = [(w, i) for i, w in enumerate(ones)]
    t_tuple = [(w, i * 10) for i, w in enumerate(tens, 2)]

    numwords = dict(o_tuple + t_tuple)
    tokens = _re_number.split(value)

    numbers = [_f for _f in (numwords.get(word) for word in tokens) if _f]
    return sum(numbers) if numbers else None


_re_packs = re.compile(r'[^a-z0-9]+(?:(cd|part).*?\d+)?', flags=re.I)


@purge.args
def packs(nameurls):
    packs = {}
    for urlname, url in nameurls:
        urlname = name(urlname)
        urlname = os.path.splitext(urlname)[0].strip()
        urlname = _re_packs.sub('_', urlname).strip('_')

        if not urlname:
            urlname = "Unknown"

        packs.setdefault(urlname, []).append(url)

    return packs


_re_size = re.compile(r'(?P<S>[\d.,]+)\s*(?P<U>[a-zA-Z]*)')


@iterate
@purge.args
def size(value, unit=None):  #: returns integer bytes
    m = _re_size.match(value)
    if not m:
        return None

    if unit is None:
        unit = m.group('U') or "byte"

    size = float(m.group('S').replace(',', '.'))
    unit = unit[0].lower()

    return convert.size(size, unit, 'byte')


_re_time = re.compile(r'(\d+|[a-zA-Z-]+)\s*(day|hr|hour|min|sec)|(\d+)')


@iterate
@purge.args
def time(value):
    value = value.lower()
    timewords = ("this", "a", "an", "next")
    pattr = r'({0})\s+day|today|daily'.format('|'.join(timewords))
    m = re.search(pattr, value)
    if m:
        res = to_midnight()
    else:
        timemap = {'day': 43200, 'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1}
        seconds = [(w in timewords or convert.to_int(i or w, 0) or number(w) or 1) *
                   timemap.get(u, 1) for w, u, i in _re_time.findall(value)]
        res = sum(seconds)
    return res
