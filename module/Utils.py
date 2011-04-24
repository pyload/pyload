# -*- coding: utf-8 -*-

""" Store all usefull functions here """

import os
import sys
import time
import re
from os.path import join

def chmod(*args):
    try:
        os.chmod(*args)
    except:
        pass

def decode(string):
    """ decode string with utf if possible """
    try:
        return string.decode("utf8", "ignore")
    except:
        return string

def removeChars(string, repl):
    """ removes all chars in repl from string"""
    if type(string) == str:
        return string.translate(None, repl)
    elif type(string) == unicode:
        return string.translate(dict([(ord(s), None) for s in repl]))

def save_join(*args):
    """ joins a path, encoding aware """
    paths = []
    for i, path in enumerate(args):
        # remove : for win comp, but not for first segment
        if i:
            path = path.replace(":","")

        path = decode(path)

        tmp = path.encode(sys.getfilesystemencoding(), "replace")
        paths.append(tmp)
    return join(*paths)

def compare_time(start, end):
    start = map(int, start)
    end = map(int, end)

    if start == end: return True

    now = list(time.localtime()[3:5])
    if start < now and end > now: return True
    elif start > end and (now > start or now < end): return True
    elif start < now and end < now and start > end: return True
    else: return False

def formatSize(size):
    """formats size of bytes"""
    size = int(size)
    steps = 0
    sizes = ["B", "KiB", "MiB", "GiB", "TiB"]
    while size > 1000:
        size /= 1024.0
        steps += 1
    return "%.2f %s" % (size, sizes[steps])

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

def parseFileSize(string): #returns bytes
    string = string.strip().lower()
    p = re.compile(r"(\d+[\.,]\d+)(.*)")
    m = p.match(string)
    if m:
        traffic = float(m.group(1).replace(",", "."))
        unit = m.group(2).strip()
        if unit in ("gb", "gig", "gbyte", "gigabyte", "gib"):
            traffic *= 1 << 30
        elif unit in ("mb", "mbyte", "megabyte", "mib"):
            traffic *= 1 << 20
        elif unit in ("kb", "kib", "kilobyte", "kbyte"):
            traffic *= 1 << 10
        return traffic

    return 0

if __name__ == "__main__":
    print freeSpace(".")

    print replace("ab'cdgdsf''ds'", "'ghd")
