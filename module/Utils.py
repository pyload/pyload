# -*- coding: utf-8 -*-

""" Store all usefull functions here """

import sys
import time
from os.path import join

def save_join(*args):
    """ joins a path, encoding aware """
    paths = []
    for i, path in enumerate(args):
        # remove : for win comp, but not for first segment
        if i:
            path = path.replace(":","")

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

def freeSpace(folder):
    if sys.platform == 'nt':
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value / 1024 / 1024 #megabyte
    else:
        from os import statvfs

        s = statvfs(folder)
        return s.f_bsize * s.f_bavail / 1024 / 1024 #megabyte

if __name__ == "__main__":
    print freeSpace(".")