# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import gettext
import io
import socket

from future import standard_library
standard_library.install_aliases()

from .layer.legacy import hashlib_ as hashlib
from .path import bufsize


try:
    import zlib
except ImportError:
    pass


__all__ = ['checksum', 'forward', 'install_translation']


def _crcsum(path, name, buffer):
    last = 0
    call = getattr(zlib, name)
    with io.open(path, mode='rb') as fp:
        for chunk in iter(lambda: fp.read(buffer), b''):
            last = call(chunk, last)
    return "{0:x}".format(last & 0xffffffff)


def _hashsum(path, name, buffer):
    h = hashlib.new(name)
    buffer *= h.block_size
    with io.open(path, mode='rb') as fp:
        for chunk in iter(lambda: fp.read(buffer), b''):
            h.update(chunk)
    return h.hexdigest()


def checksum(path, name, buffer=None):
    res = None
    buf = buffer or bufsize(path)
    if name in ('adler32', 'crc32'):
        res = _crcsum(path, name, buf)
    elif name in hashlib.algorithms_available:
        res = _hashsum(path, name, buf)
    return res


def forward(source, destination, buffer=1024):
    try:
        rawdata = source.recv(buffer)
        while rawdata:
            destination.sendall(rawdata)
            rawdata = source.recv(buffer)
    finally:
        destination.shutdown(socket.SHUT_WR)


def install_translation(domain, localedir=None, languages=None,
                        class_=None, fallback=False, codeset=None):
    try:
        trans = gettext.translation(
            domain, localedir, languages, class_, False, codeset)
    except (IOError, OSError):
        if not fallback:
            raise
        trans = gettext.translation(
            domain, localedir, None, class_, fallback, codeset)
    try:
        trans.install(unicode=True)
    except TypeError:
        trans.install()
