# -*- coding: utf-8 -*-
# @author: vuolter

""" Store all useful functions here """

import os
import re
import sys
import time

# from gettext import gettext
import pylgettext as gettext
from htmlentitydefs import name2codepoint
from os.path import join
from string import maketrans
from urllib import unquote

# abstraction layer for json operations
try:
    import simplejson as json
except ImportError:
    import json

json_loads = json.loads
json_dumps = json.dumps


def chmod(*args):
    try:
        os.chmod(*args)
    except Exception:
        pass


def decode(string):
    """ Decode string to unicode with utf8 """
    if type(string) == str:
        return string.decode("utf8", "replace")
    else:
        return string


def encode(string):
    """ Decode string to utf8 """
    if type(string) == unicode:
        return string.encode("utf8", "replace")
    else:
        return string


def remove_chars(string, repl):
    """ removes all chars in repl from string"""
    if type(repl) == unicode:
        for badc in list(repl):
            string = string.replace(badc, "")
        return string
    else:
        if type(string) == str:
            return string.translate(maketrans("", ""), repl)
        elif type(string) == unicode:
            return string.translate(dict((ord(s), None) for s in repl))


def safe_filename(name):
    """ remove bad chars """
    name = unquote(name).encode('ascii', 'replace')  # Non-ASCII chars usually breaks file saving. Replacing.
    if os.name == 'nt':
        return remove_chars(name, u'\00\01\02\03\04\05\06\07\10\11\12\13\14\15\16\17\20\21\22\23\24\25\26\27\30\31\32'
                                  u'\33\34\35\36\37/?%*|"<>')
    else:
        return remove_chars(name, u'\0\\"')


#: Deprecated method
def save_path(name):
    return safe_filename(name)


def fs_join(*args):
    """ joins a path, encoding aware """
    return fs_encode(join(*[x if type(x) == unicode else decode(x) for x in args]))


#: Deprecated method
def save_join(*args):
    return fs_join(*args)


# File System Encoding functions:
# Use fs_encode before accesing files on disk, it will encode the string properly

if sys.getfilesystemencoding().startswith('ANSI'):


    def fs_encode(string):
        return safe_filename(encode(string))

    fs_decode = decode  # decode utf8

else:
    fs_encode = fs_decode = lambda x: x  # do nothing


def get_console_encoding(enc):
    if os.name == "nt":
        if enc == "cp65001":  # aka UTF-8
            print "WARNING: Windows codepage 65001 is not supported."
            enc = "cp850"
    else:
        enc = "utf8"

    return enc


def compare_time(start, end):
    start = map(int, start)
    end = map(int, end)

    if start == end: return True

    now = list(time.localtime()[3:5])
    if start < now < end: return True
    elif start > end and (now > start or now < end): return True
    elif start < now > end < start: return True
    else: return False


def formatSize(size):
    """formats size of bytes"""
    size = int(size)
    steps = 0
    sizes = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    while size > 1000:
        size /= 1024.0
        steps += 1
    return "%.2f %s" % (size, sizes[steps])


def formatSpeed(speed):
    return formatSize(speed) + "/s"


def freeSpace(folder):
    if os.name == "nt":
        import ctypes

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        s = os.statvfs(folder)
        return s.f_frsize * s.f_bavail


def fs_bsize(path):
    """ get optimal file system buffer size (in bytes) for I/O calls """
    path = fs_encode(path)

    if os.name == "nt":
        import ctypes

        drive = "%s\\" % os.path.splitdrive(path)[0]
        cluster_sectors, sector_size = ctypes.c_longlong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(ctypes.c_wchar_p(drive), ctypes.pointer(cluster_sectors), ctypes.pointer(sector_size), None, None)
        return cluster_sectors * sector_size
    else:
        return os.statvfs(path).f_frsize


def uniqify(seq):  #: Originally by Dave Kirby
    """ Remove duplicates from list preserving order """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def parseFileSize(string, unit=None):  # returns bytes
    if not unit:
        m = re.match(r"([\d.,]+) *([a-zA-Z]*)", string.strip().lower())
        if m:
            traffic = float(m.group(1).replace(",", "."))
            unit = m.group(2)
        else:
            return 0
    else:
        if isinstance(string, basestring):
            traffic = float(string.replace(",", "."))
        else:
            traffic = string

    # ignore case
    unit = unit.lower().strip()

    if unit in ("eb", "ebyte", "exabyte", "eib", "e"):
        traffic *= 1 << 60
    elif unit in ("pb", "pbyte", "petabyte", "pib", "p"):
        traffic *= 1 << 50
    elif unit in ("tb", "tbyte", "terabyte", "tib", "t"):
        traffic *= 1 << 40
    elif unit in ("gb", "gbyte", "gigabyte", "gib", "g", "gig"):
        traffic *= 1 << 30
    elif unit in ("mb", "mbyte", "megabyte", "mib", "m"):
        traffic *= 1 << 20
    elif unit in ("kb", "kbyte", "kilobyte", "kib", "k"):
        traffic *= 1 << 10

    return traffic


def lock(func):


    def new(*args):
        # print "Handler: %s args: %s" % (func, args[1:])
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
                return unichr(int(text[3:-1], 16))
            else:
                return unichr(int(text[2:-1]))
        except ValueError:
            pass
    else:
        # named entity
        try:
            name = text[1:-1]
            text = unichr(name2codepoint[name])
        except KeyError:
            pass

    return text  # leave as is


def has_method(obj, name):
    """ Check if "name" was defined in obj, (false if it was inhereted) """
    return hasattr(obj, '__dict__') and name in obj.__dict__


def html_unescape(text):
    """Removes HTML or XML character references and entities from a text string"""
    return re.sub("&#?\w+;", fixup, text)


def versiontuple(v):  #: By kindall (http://stackoverflow.com/a/11887825)
    return tuple(map(int, (v.split("."))))


def load_translation(name, locale, default="en"):
    """ Load language and return its translation object or None """
    from traceback import print_exc
    from os.path import join
    try:
        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation(name, join(pypath, "locale"),
                                          languages=[locale, default], fallback=True)
    except Exception:
        print_exc()
        return None
    else:
        translation.install(True)
        return translation
