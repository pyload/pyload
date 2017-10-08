# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import socket

from future import standard_library
from future.builtins import map

from pyload.utils.check import ismapping

standard_library.install_aliases()


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
    return type(obj)(
        map(reversed, obj.items())) if ismapping(obj) else reversed(obj)


def forward(source, destination, buffering=1024):
    try:
        rawdata = source.recv(buffering)
        while rawdata:
            destination.sendall(rawdata)
            rawdata = source.recv(buffering)
    finally:
        destination.shutdown(socket.SHUT_WR)


# def get_translation(domain, localedir=None, languages=None, class_=None,
        # fallback=False, codeset=None):
    # try:
        # trans = gettext.translation(
        # domain, localedir, languages, class_, False, codeset)
    # except (IOError, OSError):
        # if not fallback:
        # raise
        # trans = gettext.translation(
        # domain, localedir, None, class_, fallback, codeset)
    # return trans


# def install_translation(domain, localedir=None, languages=None,
        # class_=None, fallback=False, codeset=None):
    # trans = get_translation(
        # domain, localedir, languages, class_, fallback, codeset)
    # try:
        # trans.install(str=True)
    # except TypeError:
        # trans.install()
