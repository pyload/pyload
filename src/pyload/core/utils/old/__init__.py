# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import os
import random
import re
import string
import sys
import time
import requests_html
from html.entities import name2codepoint
import html.parser
import unicodedata
import datetime
from datetime import timedelta
import shutil
import urllib.parse
from functools import partial, wraps
from .... import exc_logger

from .. import purge

try:
    import send2trash
except ImportError:
    send2trash = None


# Hotfix UnicodeDecodeError: 'ascii' codec can't decode..
def normalize(value):
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore")


# NOTE: Revert to `decode` in Python 3
def decode(value):
    """
    Encoded string (default to own system encoding) -> unicode string.
    """
    try:
        return str(value)
    except UnicodeEncodeError:
        return normalize(value)


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

        dirname, basename = os.path.split(filename)
        name, ext = os.path.splitext(basename)
        path = drive + dirname + purge.truncate(name, 259) + ext

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
    repl = '<>:"/\\|?*' if os.name == "nt" else '\0/\\"'
    name = purge.chars(value, repl)
    return name


def fixurl(url, unquote=None):
    old = url
    url = urllib.parse.unquote(url)

    if unquote is None:
        unquote = url is old

    url = decode(url)
    # try:
    # url = url.decode("unicode-escape")
    # except UnicodeDecodeError:
    # pass

    url = html_unescape(url)
    url = re.sub(r"(?<!:)/{2,}", "/", url).strip().lstrip(".")

    if not unquote:
        url = urllib.parse.quote(url)

    return url


def parse_name(value, safechar=True):
    path = fixurl(decode(value), unquote=False)
    url_p = urllib.parse.urlparse(path.rstrip("/"))
    name = (
        url_p.path.split("/")[-1]
        or url_p.query.split("=", 1)[::-1][0].split("&", 1)[0]
        or url_p.netloc.split(".", 1)[0]
    )

    name = urllib.parse.unquote(name)
    return safename(name) if safechar else name


# NOTE: decorator
def lock(func=None, *decor_args, **decor_kwargs):
    if func is None:
        return partial(lock, *decor_args, **decor_kwargs)

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.lock.acquire(*decor_args, **decor_kwargs)
        try:
            return func(self, *args, **kwargs)
        finally:
            self.lock.release()

    return wrapper


def html_unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    """
    h = html.parser.HTMLParser()
    return h.unescape(text)
