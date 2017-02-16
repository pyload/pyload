# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import absolute_import, print_function, unicode_literals
from __future__ import division

from future import standard_library
standard_library.install_aliases()
import gettext
import io
import os
import socket
from builtins import PACKDIR

from pyload.utils.lib import hashlib
from pyload.utils.path import bufsize

try:
    import zlib
except ImportError:
    pass


def checksum(path, name, buffer=None):
    res = None
    buf = buffer or bufsize(path)

    if name in ('adler32', 'crc32'):
        last = 0
        call = getattr(zlib, name)
        with io.open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(buf), b''):
                last = call(chunk, last)
        res = "{:x}".format(last & 0xffffffff)

    elif name in hashlib.algorithms_available:
        h = hashlib.new(name)
        buf *= h.block_size
        with io.open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(buf), b''):
                h.update(chunk)
        res = h.hexdigest()

    return res


def forward(source, destination, buffer=1024):
    try:
        rawdata = source.recv(buffer)
        while rawdata:
            destination.sendall(rawdata)
            rawdata = source.recv(buffer)
    finally:
        destination.shutdown(socket.SHUT_WR)


# TODO: Recheck in 0.8.x
def get_translation(domain, language, default=None):
    """
    Load language and return its translation object or None.
    """
    localedir = os.path.join(PACKDIR, "locale")
    languages = [language, default]
    return gettext.translation(domain, localedir, languages, fallback=True)
