# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

import os
import re

from future import standard_library

from pyload.utils.new import convert, format, purge
from pyload.utils.new.lib import hashlib

standard_library.install_aliases()




@iterate
def alias(value):
    chunks = re.split(r'[\d.-_]+', format.name(value))
    return ''.join(word.capitalize() for word in chunks if word)


@iterate
@purge.args
def boolean(value):
    return re.match(r'1|y|true', value, re.I) is not None


@iterate
def entries(value):
    return [entry for entry in re.sub(r'[;,\s]+', '|', value).split('|') if entry]


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
    from pyload.utils.new.web import check as webcheck
    if webcheck.isurl(value):
        from pyload.utils.new.web import convert as webconvert
        return webconvert.url_to_name(value)
    else:
        return os.path.basename(value)


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
    tokens = re.split(r'[\s-]+', value)

    numbers = filter(None, (numwords.get(word) for word in tokens))
    return sum(numbers) if numbers else None


@purge.args
def packages(packages):
    packs = {}
    regex = re.compile(r'[^a-zA-Z0-9]+(?:(cd|part).*?\d+)?', flags=re.I)
    for urlname, url in packages:
        urlname = name(urlname)
        urlname = os.path.splitext(urlname)[0].strip()
        urlname = regex.sub('_', urlname).strip('_')

        if not urlname:
            urlname = "Unknown"

        packs.setdefault(urlname, []).append(url)

    return packs


@iterate
@purge.args
def size(value, unit=None):  #: returns integer bytes
    m = re.match(r'(?P<S>[\d.,]+)\s*(?P<U>[a-zA-Z]*)', value)
    if not m:
        return None

    if unit is None:
        unit = m.group('U') or "byte"

    size = float(m.group('S').replace(',', '.'))
    unit = unit[0].lower()

    return convert.size(size, unit, 'byte')


@iterate
@purge.args
def time(value):
    value = value.lower()
    timewords = ("this", "a", "an", "next")
    pattr = r'({})\s+day|today|daily'.format('|'.join(timewords))
    m = re.search(pattr, value)
    if m:
        res = to_midnight()
    else:
        regex = re.compile(r'(\d+|[a-zA-Z-]+)\s*(day|hr|hour|min|sec)|(\d+)')
        timemap = {'day': 43200, 'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1}
        seconds = [(w in timewords or convert.to_int(i or w, 0) or number(w) or 1) *
                   timemap.get(u, 1) for w, u, i in regex.findall(value)]
        res = sum(seconds)
    return res
