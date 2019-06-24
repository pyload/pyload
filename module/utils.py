# -*- coding: utf-8 -*-

""" Store all usefull functions here """

import os
import sys
import time
import re
from os.path import join
from string import maketrans
from htmlentitydefs import name2codepoint

def chmod(*args):
    try:
        os.chmod(*args)
    except:
        pass


def decode(string):
    """ decode string with utf if possible """
    try:
        return string.decode("utf8", "replace")
    except:
        return string


def remove_chars(string, repl):
    """ removes all chars in repl from string"""
    if type(string) == str:
        return string.translate(maketrans("", ""), repl)
    elif type(string) == unicode:
        return string.translate(dict([(ord(s), None) for s in repl]))


def save_path(name):
    #remove some chars
    if os.name == 'nt':
        return remove_chars(name, '/\\?%*:|"<>')
    else:
        return remove_chars(name, '/\\"')


def save_join(*args):
    """ joins a path, encoding aware """
    return fs_encode(join(*[x if type(x) == unicode else decode(x) for x in args]))


# File System Encoding functions:
# Use fs_encode before accesing files on disk, it will encode the string properly

if sys.getfilesystemencoding().startswith('ANSI'):
    def fs_encode(string):
        try:
            string = string.encode('utf-8')
        finally:
            return string

    fs_decode = decode #decode utf8

else:
    fs_encode = fs_decode = lambda x: x  # do nothing

def get_console_encoding(enc):
    if os.name == "nt":
        if enc == "cp65001":  # aka UTF-8
            print "WARNING: Windows codepage 65001 is not supported."
            enc = "cp850"

        elif enc is None:  #: piped
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
    sizes = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
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
        from os import statvfs

        s = statvfs(folder)
        return s.f_bsize * s.f_bavail


def uniqify(seq, idfun=None):
# order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def parseFileSize(string, unit=None): #returns bytes
    if not unit:
        m = re.match(r"(\d*[\.,]?\d+)(.*)", string.strip().lower())
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

    #ignore case
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
        #print "Handler: %s args: %s" % (func,args[1:])
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

    return text # leave as is


def html_unescape(text):
    """Removes HTML or XML character references and entities from a text string"""
    return re.sub("&#?\w+;", fixup, text)

if __name__ == "__main__":
    print freeSpace(".")

    print remove_chars("ab'cdgdsf''ds'", "'ghd")
