# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import gettext
import os
import socket
from builtins import map

from future import standard_library

from .check import ismapping
from .fs import blksize, lopen
from .layer.legacy import hashlib_ as hashlib

standard_library.install_aliases()


try:
    import zlib
except ImportError:
    pass


def accumulate(iterable, inv_map=None):
    """
    Accumulate (key, value) data to {value : [key]} dictionary.
    """
    if inv_map is None:
        inv_map = {}
    for key, value in iterable:
        inv_map.setdefault(value, []).append(key)
    return inv_map


def reverse(obj):
    return type(obj)(map(reversed, obj.items())) if ismapping else reversed(obj)


def _crcsum(filename, chkname, buffer):
    last = 0
    call = getattr(zlib, chkname)
    with lopen(filename, mode='rb') as fp:
        for chunk in iter(lambda: fp.read(buffer), b''):
            last = call(chunk, last)
    return "{0:x}".format(last & 0xffffffff)


def _hashsum(filename, chkname, buffer):
    h = hashlib.new(chkname)
    buffer *= h.block_size
    with lopen(filename, mode='rb') as fp:
        for chunk in iter(lambda: fp.read(buffer), b''):
            h.update(chunk)
    return h.hexdigest()


def checksum(filename, chkname, buffer=None):
    res = None
    buf = buffer or blksize(filename)
    if chkname in ('adler32', 'crc32'):
        res = _crcsum(filename, chkname, buf)
    elif chkname in hashlib.algorithms_available:
        res = _hashsum(filename, chkname, buf)
    return res


def forward(source, destination, buffer=1024):
    try:
        rawdata = source.recv(buffer)
        while rawdata:
            destination.sendall(rawdata)
            rawdata = source.recv(buffer)
    finally:
        destination.shutdown(socket.SHUT_WR)


def get_translation(domain, localedir=None, languages=None, class_=None,
                    fallback=False, codeset=None):
    try:
        trans = gettext.translation(
            domain, localedir, languages, class_, False, codeset)
    except (IOError, OSError):
        if not fallback:
            raise
        trans = gettext.translation(
            domain, localedir, None, class_, fallback, codeset)
    return trans


def install_translation(domain, localedir=None, languages=None,
                        class_=None, fallback=False, codeset=None):
    trans = get_translation(
        domain, localedir, languages, class_, fallback, codeset)
    try:
        trans.install(str=True)
    except TypeError:
        trans.install()
