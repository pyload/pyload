# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import gettext
import itertools
import os
import socket
import zlib

from pyload.utils.new import format
from pyload.utils.new.lib import hashlib
from pyload.utils.new.path import fsbsize, open


def checksum(path, name, buffer=None):
    res = None
    buf = buffer or bufsize(path)

    if name in ('adler32', 'crc32'):
        last = 0
        call = getattr(zlib, name)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(buf), b''):
                last = call(chunk, last)
        res = "{:x}".format(last & 0xffffffff)

    elif name in hashlib.algorithms_available:
        h = hashlib.new(name)
        buf *= h.block_size
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(buf), b''):
                h.update(chunk)
        res = h.hexdigest()

    return res


def forward(source, destination):
    try:
        bufsize = 1024
        bufdata = source.recv(bufsize)
        while bufdata:
            destination.sendall(bufdata)
            bufdata = source.recv(bufsize)
    finally:
        destination.shutdown(socket.SHUT_WR)


# TODO: Recheck in 0.8.x
def get_translation(domain, language, default=None):
    """
    Load language and return its translation object or None.
    """
    localedir = os.path.join(ROOTDIR, "locale")
    languages = [language, default]
    return gettext.translation(domain, localedir, languages, fallback=True)
