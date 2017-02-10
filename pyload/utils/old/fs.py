# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import sys
from os.path import join

from pyload.utils import purge
from pyload.utils.old import decode

# File System Encoding functions:
# Use fs_encode before accessing files on disk, it will encode the string
# properly

if sys.getfilesystemencoding().startswith('ANSI'):
    def fs_encode(string):
        if isinstance(string, str):
            return string.encode('utf8')
        else:
            return string

    fs_decode = decode  # decode utf8

else:
    fs_encode = fs_decode = lambda x: x  # do nothing

# FS utilities


def chmod(path, mode):
    try:
        return os.chmod(fs_encode(path), mode)
    except Exception:
        pass


def dirname(path):
    return fs_decode(os.path.dirname(fs_encode(path)))


def abspath(path):
    return fs_decode(os.path.abspath(fs_encode(path)))


def chown(path, uid, gid):
    return os.chown(fs_encode(path), uid, gid)


def remove(path):
    return os.remove(fs_encode(path))


def exists(path):
    return os.path.exists(fs_encode(path))


def makedirs(path, mode=0o755):
    return os.makedirs(fs_encode(path), mode)


def listdir(path):
    return [fs_decode(x) for x in os.listdir(fs_encode(path))]


def safe_filename(name):
    # remove some chars
    if os.name == 'nt':
        return purge.chars(name, '/\\?%*:;|"<>,')
    else:
        return purge.chars(name, '/\\"')


def stat(name):
    return os.stat(fs_encode(name))


def safe_join(*args):
    """
    Joins a path, encoding aware.
    """
    return fs_encode(
        join(*[x if isinstance(x, str) else decode(x) for x in args]))


def save_join(*args):
    return safe_join(*args)


def free_space(folder):
    folder = fs_encode(folder)

    if os.name == 'nt':
        import ctypes

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        s = os.statvfs(folder)
        return s.f_frsize * s.f_bavail


def get_bsize(path):
    """
    Get optimal file system buffer size (in bytes) for i/o calls.
    """
    path = fs_encode(path)

    if os.name == 'nt':
        import ctypes

        drive = "{}\\".format(os.path.splitdrive(path)[0])
        cluster_sectors, sector_size = ctypes.c_longlong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(ctypes.c_wchar_p(drive), ctypes.pointer(
            cluster_sectors), ctypes.pointer(sector_size), None, None)
        return cluster_sectors * sector_size
    else:
        return os.statvfs(path).f_bsize
