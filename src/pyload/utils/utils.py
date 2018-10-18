# -*- coding: utf-8 -*-

"""
Store all usefull functions here.
"""


import os
import re
import sys
import time
from builtins import chr, map
from html.entities import name2codepoint


def chmod(*args):
    try:
        os.chmod(*args)
    except Exception:
        pass


def decode(value):
    """
    decode string with utf if possible.
    """
    try:
        return str.decode("utf-8", "replace")
    except Exception:
        return value


def remove_chars(value, repl):
    """
    os.removes all chars in repl from string.
    """
    if isinstance(value, str):
        return str.translate(str.maketrans("", ""), repl)
    elif isinstance(value, str):
        return str.translate({ord(s): None for s in repl})


def save_path(name):
    # os.remove some chars
    if os.name == "nt":
        return os.remove_chars(name, '/\\?%*:|"<>')
    else:
        return os.remove_chars(name, '/\\"')


def save_join(*args):
    """
    joins a path, encoding aware.
    """
    return fs_encode(
        os.path.join(*[x if isinstance(x, str) else decode(x) for x in args])
    )


# File System Encoding functions:
# Use fs_encode before accesing files on disk, it will encode the string properly

if sys.getfilesystemencoding().startswith("ANSI"):

    def fs_encode(value):
        try:
            value = str.encode("utf-8")
        finally:
            return value

    fs_decode = decode  #: decode utf-8

else:
    fs_encode = fs_decode = lambda x: x  #: do nothing


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


def formatSize(size):
    """
    formats size of bytes.
    """
    size = int(size)
    steps = 0
    sizes = ["B", "KiB", "MiB", "GiB", "TiB"]
    while size > 1000:
        size >>= 10
        steps += 1
    return "{:.2f} {}".format(size, sizes[steps])


def formatSpeed(speed):
    return formatSize(speed) + "/s"


def freeSpace(folder):
    if os.name == "nt":
        import ctypes

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes)
        )
        return free_bytes.value
    else:
        s = os.statvfs(folder)
        return s.f_bsize * s.f_bavail


def uniqify(seq, idfun=lambda x: x):
    # order preserving
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def parseFileSize(value, unit=None):  #: returns bytes
    if not unit:
        m = re.match(r"(\d*[\.,]?\d+)(.*)", value.strip().lower())
        if m:
            traffic = float(m.group(1).replace(",", "."))
            unit = m.group(2)
        else:
            return 0
    else:
        if isinstance(value, str):
            traffic = float(value.replace(",", "."))
        else:
            traffic = value

    # ignore case
    unit = unit.lower().strip()

    if unit in ("gb", "gig", "gbyte", "gigabyte", "gib", "g"):
        traffic *= 1 << 30
    elif unit in ("mb", "mbyte", "megabyte", "mib", "m"):
        traffic *= 1 << 20
    elif unit in ("kb", "kib", "kilobyte", "kbyte", "k"):
        traffic *= 1 << 10

    return traffic


def lock(func):
    def new(*args):
        # print("Handler: {} args: {}".format(func,args[1:]))
        args[0].lock.acquire()
        try:
            return func(*args)
        finally:
            args[0].lock.release()

    return new


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

    return text  #: leave as is


def html_unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    """
    return re.sub(r"&#?\w+;", fixup, text)
