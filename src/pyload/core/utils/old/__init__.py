# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import os
import re
import unicodedata
import urllib.parse
from functools import partial, wraps

from .. import purge
from ..web.purge import unescape as html_unescape

try:
    import send2trash
except ImportError:
    send2trash = None


# def save_join(*args):
# """
# joins a path, encoding aware.
# """
# return fs_encode(
# os.path.join(*[x if isinstance(x, str) else decode(x) for x in args])
# )


# TODO: Remove in 0.6.x
def safepath(value):
    """
    Remove invalid characters and truncate the path if needed.
    """
    drive, filename = os.path.splitdrive(value)

    filesep = os.sep if os.path.isabs(filename) else ""
    fileparts = (safename(name) for name in filename.split(os.sep))

    filename = os.path.join(filesep, *fileparts)
    path = drive + filename

    try:
        if os.name != "nt":
            return

        excess_chars = len(path) - 259
        if excess_chars < 1:
            return

        dirname, basename = os.path.split(filename)
        name, ext = os.path.splitext(basename)
        path = drive + dirname + purge.truncate(name, len(name) - excess_chars) + ext

    finally:
        return path


def safejoin(*args):
    """
    os.path.join + safepath.
    """
    return safepath(os.path.join(*args))


def safename(value):
    """
    Remove invalid characters.
    """
    # repl = '<>:"/\\|?*' if os.name == "nt" else '\0/\\"'
    repl = '<>:"/\\|?*\0'
    name = purge.chars(value, repl)
    return name


def fixurl(url, unquote=None):
    old = url
    url = urllib.parse.unquote(url)

    if unquote is None:
        unquote = url == old

    # try:
    # url = url.decode("unicode-escape")
    # except UnicodeDecodeError:
    # pass

    url = html_unescape(url)
    url = re.sub(r"(?<!:)/{2,}", "/", url).strip().lstrip(".")

    if not unquote:
        url = urllib.parse.quote(url)

    return url
