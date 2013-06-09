# -*- coding: utf-8 -*-

import os
import sys
from os.path import join
from . import decode, remove_chars

# File System Encoding functions:
# Use fs_encode before accessing files on disk, it will encode the string properly

if sys.getfilesystemencoding().startswith('ANSI'):
    def fs_encode(string):
        if type(string) == unicode:
            return string.encode('utf8')
        return string

    fs_decode = decode #decode utf8

else:
    fs_encode = fs_decode = lambda x: x  # do nothing

# FS utilities
def chmod(path, mode):
    try:
        return os.chmod(fs_encode(path), mode)
    except :
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

def makedirs(path, mode=0755):
    return os.makedirs(fs_encode(path), mode)

# fs_decode?
def listdir(path):
    return [fs_decode(x) for x in os.listdir(fs_encode(path))]

def save_filename(name):
    #remove some chars
    if os.name == 'nt':
        return remove_chars(name, '/\\?%*:|"<>,')
    else:
        return remove_chars(name, '/\\"')

def stat(name):
    return os.stat(fs_encode(name))

def save_join(*args):
    """ joins a path, encoding aware """
    return fs_encode(join(*[x if type(x) == unicode else decode(x) for x in args]))

def free_space(folder):
    folder = fs_encode(folder)

    if os.name == "nt":
        import ctypes

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        from os import statvfs

        s = statvfs(folder)
        return s.f_frsize * s.f_bavail
