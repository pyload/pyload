# -*- coding: utf-8 -*-

"""
Store all useful functions here.
"""
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import map
from builtins import chr
import os
import time
import re
from string import maketrans
from itertools import islice
from html.entities import name2codepoint

# abstraction layer for json operations
try:  # since python 2.6
    import json
except ImportError:  # use system simplejson if available
    import simplejson as json

json_loads = json.loads
json_dumps = json.dumps


def decode(string):
    """
    Decode string to unicode with utf8.
    """
    if isinstance(string, str):
        return string.decode("utf8", "replace")
    else:
        return string


def encode(string):
    """
    Decode string to utf8.
    """
    if isinstance(string, str):
        return string.encode("utf8", "replace")
    else:
        return string


def remove_chars(string, repl):
    """
    Removes all chars in repl from string.
    """
    if isinstance(string, str):
        return string.translate(maketrans("", ""), repl)
    elif isinstance(string, str):
        return string.translate(dict((ord(s), None) for s in repl))


def get_console_encoding(enc):
    if os.name == 'nt':
        if enc == "cp65001":  # aka UTF-8
            print("WARNING: Windows codepage 65001 is not supported")
            enc = "cp850"
    else:
        enc = "utf8"

    return enc


def compare_time(start, end):
    start = list(map(int, start))
    end = list(map(int, end))

    if start == end:
        return True

    now = list(time.localtime()[3:5])
    if start < now < end:
        return True
    elif start > end and (now > start or now < end):
        return True
    elif start < now > end < start:
        return True
    else:
        return False


def to_list(value):
    return value if isinstance(value, list) else list(value) if isinstance(value, set) else (
        [value] if value is not None else [])


def format_size(bytes):
    bytes = int(bytes)
    steps = 0
    sizes = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    while bytes > 1000:
        bytes /= 1024.0
        steps += 1
    return "{:.2f} {}".format(bytes, sizes[steps])


def format_speed(speed):
    return format_size(speed) + "/s"


def format_time(seconds):
    if seconds < 0:
        return "00:00:00"
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:.2d}:{:.2d}:{:.2d}".format(hours, minutes, seconds)


def parse_time(timestamp, pattern):
    """
    Parse a string representing a time according to a pattern and
    return a time in seconds suitable for an account plugin.
    """
    return int(time.mktime(time.strptime(timestamp, pattern)))


def parse_size(string, unit=None):
    """
    Parses file size from a string.
    Tries to parse unit if not given.

    :return: size in bytes
    """
    if not unit:
        m = re.match(r"([\d.,]+) *([a-zA-Z]*)", string.strip().lower())
        if m:
            traffic = float(m.group(1).replace(",", "."))
            unit = m.group(2)
        else:
            return 0
    else:
        if isinstance(string, str):
            traffic = float(string.replace(",", "."))
        else:
            traffic = string

    # ignore case
    unit = unit.lower().strip()

    if unit in ("gb", "gig", "gbyte", "gigabyte", "gib", "g"):
        traffic *= 1 << 30
    elif unit in ("mb", "mbyte", "megabyte", "mib", "m"):
        traffic *= 1 << 20
    elif unit in ("kb", "kib", "kilobyte", "kbyte", "k"):
        traffic *= 1 << 10

    return traffic


def uniqify(seq):  # by Dave Kirby
    """
    Removes duplicates from list, preserve order.
    """
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def bits_set(bits, compare):
    """
    Checks if all bits are set in compare, or bits is 0.
    """
    return bits == (bits & compare)


def lock(func):
    def new(*args, **kwargs):
        # print("Handler: {} args: {}".format(func, args[1:]))
        args[0].lock.acquire()
        try:
            return func(*args, **kwargs)
        finally:
            args[0].lock.release()

    return new


def read_lock(func):
    def new(*args, **kwargs):
        args[0].lock.acquire(shared=True)
        try:
            return func(*args, **kwargs)
        finally:
            args[0].lock.release()

    return new


def chunks(iterable, size):
    it = iter(iterable)
    item = list(islice(it, size))
    while item:
        yield item
        item = list(islice(it, size))


def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
        # character reference
        try:
            if text[:3] == "&#x":
                return chr(int(text[3:-1], 16))
            else:
                return chr(int(text[2:-1]))
        except ValueError:
            pass
    else:
        # named entity
        try:
            name = text[1:-1]
            text = chr(name2codepoint[name])
        except KeyError:
            pass

    return text  # leave as is


def has_method(obj, name):
    """
    Checks if 'name' was defined in obj, (false if it was inhereted).
    """
    return hasattr(obj, '__dict__') and name in obj.__dict__


def accumulate(it, inv_map=None):
    """
    Accumulate (key, value) data to {value : [keylist]} dictionary.
    """
    if inv_map is None:
        inv_map = {}

    for key, value in it:
        if value in inv_map:
            inv_map[value].append(key)
        else:
            inv_map[value] = [key]

    return inv_map


def to_string(value):
    return str(value) if not isinstance(value, str) and not isinstance(value, bytes) else value


def to_bool(value):
    if not isinstance(value, str):
        return True if value else False
    return True if value.lower() in ("1", "true", "on", "an", "yes") else False


def to_int(string, default=0):
    """
    Return int from string or default.
    """
    try:
        return int(string)
    except ValueError:
        return default


def get_index(l, value):
    """
    .index method that also works on tuple and python 2.5.
    """
    for pos, t in enumerate(l):
        if t == value:
            return pos

    # Matches behavior of list.index
    raise ValueError("list.index(x): x not in list")


def primary_uid(user):
    """
    Gets primary user id for user instances or ints.
    """
    if isinstance(user, int):
        return user
    return user.primary if user else None


def html_unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    """
    return re.sub("&#?\w+;", fixup, text)


def try_catch(fallback):
    """
    Decorator that executes the function and returns the value or fallback on any exception.
    """
    def wrap(f):
        def new(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                return fallback

        return new

    return wrap
