# -*- coding: utf-8 -*-

import random
import socket
import string

import requests_html

from .check import is_mapping


def random_string(length):
    seq = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(seq) for _ in range(length))


def is_plural(value):
    try:
        n = abs(float(value))
        return n == 0 or n > 1
    except ValueError:
        return value.endswith("s")  # TODO: detect uncommon plurals


def eval_js(script):
    return requests_html.HTML().render(script=script, reload=False)


def accumulate(iterable, to_map=None):
    """
    Accumulate (key, value) data to {value : [key]} dictionary.
    """
    if to_map is None:
        to_map = {}
    for key, value in iterable:
        to_map.setdefault(value, []).append(key)
    return to_map


def reversemap(obj):
    """
    Invert mapping object preserving type and ordering.
    """
    return obj.__class__(reversed(item) for item in obj.items())


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
