# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import io
import os
import shutil
from builtins import int, next
from os.path import *

import psutil
from future import standard_library
standard_library.install_aliases()

from .check import ismodule
from .decorator import iterate


try:
    import magic
except ImportError:
    from filetype import guess_mime
try:
    import send2trash
except ImportError:
    pass


@iterate
def availspace(path):
    if os.name != 'nt':
        stat = os.statvfs(path)
        res = stat.f_frsize * stat.f_bavail
    else:
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path),
                                                   None,
                                                   None,
                                                   ctypes.pointer(free_bytes))
        res = int(free_bytes.value)
    return res


def _shdo(func, src, dst, array=None):
    try:
        func(src, dst)
    except Exception:
        pass
    else:
        if isinstance(array, list):
            del array[:]
            
            
def _shdorc(func, filenames, src_dir, dst_dir, overwrite=None):
    NT = os.name == 'nt'
    isfile = os.path.isfile
    join = os.path.join
    mtime = os.path.getmtime
    remove = os.remove
    
    for filename in filenames:
        src_file = join(src_dir, filename)
        dst_file = join(dst_dir, filename)
        try:
            if isfile(dst_file):
                if overwrite is None and mtime(
                        src_file) <= mtime(dst_file):
                    continue
                elif not overwrite:
                    continue
                elif NT:
                    remove(dst_file)
                    
            func(src_file, dst_file)
            
        except Exception:
            continue
            
            
def copy(src, dst, overwrite=None, preserve_metadata=True):
    copy = shutil.copy2 if preserve_metadata else shutil.copy
    copytree = shutil.copytree
    isdir = os.path.isdir

    if not isdir(dst) or not isdir(src):
        return copytree(src, dst)

    for src_dir, dirnames, filenames in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)
        if isdir(dst_dir):
            _shdorc(copy, filenames, src_dir, dst_dir, overwrite)
        else:
            _shdo(copytree, src_dir, dst_dir, dirnames)
            

@iterate
def exists(path, sensitive=False):
    """
    Case-sensitive os.path.exists.
    """
    if not sensitive:
        return os.path.exists(path)
    if os.path.exists(path):
        dir, name = os.path.split(path)
        return name in os.listdir(dir)
    else:
        return False


@iterate
def filesize(path):
    return os.stat(path).st_size


@iterate
def filetype(path):
    try:
        return magic.from_file(path, mime=True)
    except NameError:
        pass
    return guess_mime(path)


def flush(path):
    if not os.path.exists(path):
        raise OSError("Path not exists")
    if os.path.isfile(path):
        with io.open(path) as fp:
            fp.flush()
            os.fsync(fp.fileno())
    elif os.path.isdir(path):
        remove(os.listdir(path))
    else:
        raise TypeError


@iterate
def bufsize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    if os.name != 'nt':
        res = os.statvfs(path).f_bsize
    else:
        import ctypes
        drive = "{0}\\".format(splitdrive(abspath(path))[0])
        cluster_sectors = ctypes.c_longlong(0)
        sector_size = ctypes.c_longlong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(ctypes.c_wchar_p(drive),
                                                 ctypes.pointer(
                                                     cluster_sectors),
                                                 ctypes.pointer(sector_size),
                                                 None,
                                                 None)
        res = int(cluster_sectors.value * sector_size.value)
    return res


@iterate
def isexec(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)


def merge(dstfile, srcfile):
    buf = bufsize(srcfile)
    with io.open(dstfile, mode='ab') as dfp:
        with io.open(srcfile, mode='rb') as sfp:
            for chunk in iter(lambda: sfp.read(buf), b''):
                dfp.write(chunk)


@iterate
def mountpoint(path):
    path = os.path.realpath(os.path.abspath(path))
    while path != os.sep:
        if os.path.ismount(path):
            return path
        path = os.path.abspath(os.path.join(path, os.pardir))
    return path


@iterate
def filesystem(path):
    mp = mountpoint(path)
    fs = dict((part.mountpoint, part.fstype) for part in psutil.disk_partitions())
    return fs.get(mp)


def mkfile(path, opened=None, size=None):
    if os.path.exists(path):
        raise OSError
    mode = 'wb'
    with io.open(path, mode) as fp:
        if size and os.name == 'nt':
            fp.truncate(size)
    fp = io.open(path, opened if isinstance(opened, str) else mode)
    if not opened:
        fp.close()
    return fp


def makedirs(path, mode=0o700, exist_ok=True):
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if not exist_ok or not os.path.isdir(path):
            raise OSError(e)


def makefile(path, dirmode=0o700, opened=None, size=None):
    dirname, basename = os.path.split(path)
    makedirs(dirname, dirmode)
    return mkfile(basename, opened, size)

    
def move(src, dst, overwrite=None):
    isdir = os.path.isdir
    move = shutil.move
    removedirs = os.removedirs

    if not isdir(dst) or not isdir(src):
        return move(src, dst)

    for src_dir, dirnames, filenames in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)
        if isdir(dst_dir):
            _shdorc(move, filenames, src_dir, dst_dir, overwrite)
        else:
            _shdo(move, src_dir, dst_dir, dirnames)
        try:
            removedirs(src_dir)
        except Exception:
            pass
    try:
        os.rmdir(src)
    except Exception:
        pass

        
@iterate
def mtime(path):
    getmtime = os.path.getmtime
    join = os.path.join

    if not os.path.isdir(path):
        return getmtime(path)

    mtimes = [getmtime(join(dir, file))
              for dir, dirnames, filenames in os.walk(path)
              for file in filenames]

    return max(0, 0, *mtimes)


@iterate
def pyclean(path, recursive=True):
    join = os.path.join
    remove = os.remove
    walkpath = os.walk(path)
    if not recursive:
        walkpath = (next(walkpath),)
    for dir, dirnames, filenames in walkpath:
        dir = join(dir, '__pycache__')
        try:
            remove(dir)
        except Exception:
            pass
        for filename in filenames:
            if filename[-4:] not in ('.pyc', '.pyo', '.pyd'):
                continue
            file = join(dir, filename)
            try:
                remove(file)
            except Exception:
                continue


def remove(path, trash=False, ignore_errors=False):
    if not os.path.exists(path):
        if ignore_errors:
            return None
        raise OSError("Path not exists")
    if trash and ismodule('send2trash'):
        send2trash.send2trash(path)
    elif os.path.isdir(path):
        shutil.rmtree(path, ignore_errors)
    elif os.path.isfile(path):
        os.remove(path)
    else:
        raise TypeError


@iterate
def which(path):
    try:
        return shutil.which(path)  # NOTE: Available only under Python 3
    except AttributeError:
        pass

    dirname, basename = split(path)
    if dirname:
        return path if isexec(path) else None

    for envpath in os.environ['PATH'].split(os.pathsep):
        path = join(envpath.strip('"'), path)
        if isexec(path):
            return path


# Cleanup
del int, io, ismodule, iterate, os, psutil, shutil
try:
    del magic
except NameError:
    del guess_mime
try:
    del send2trash
except NameError:
    pass
