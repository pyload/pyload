# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from builtins import dict
from builtins import open
import io
import locale
import os
import shutil
import sys
from builtins import int, next
from contextlib import contextmanager

import portalocker
import psutil

import send2trash
from future import standard_library

standard_library.install_aliases()

try:
    import magic
except ImportError:
    from filetype import guess_mime


def availspace(path):
    if os.name != 'nt':
        stat = os.statvfs(path)
        res = stat.f_frsize * stat.f_bavail
    else:
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes))
        res = int(free_bytes.value)
    return res


def _shdo(func, src, dst, overwrite=None, ref=None):
    mtime = os.path.getmtime
    try:
        if os.path.isfile(dst):
            if (overwrite is None and mtime(src) <= mtime(dst)) or not overwrite:
                return None
            if os.name == 'nt':
                os.remove(dst)
        func(src, dst)
        if isinstance(ref, list):
            del ref[:]
    except Exception:
        pass


def _shdorc(func, filenames, src_dir, dst_dir, overwrite=None):
    join = os.path.join
    for fname in filenames:
        src_file = join(src_dir, fname)
        dst_file = join(dst_dir, fname)
        _shdo(func, src_file, dst_file, overwrite)


def _copyrc(src, dst, overwrite, preserve_metadata):
    copy = shutil.copy2 if preserve_metadata else shutil.copy
    copytree = shutil.copytree
    exists = os.path.exists
    for src_dir, dirnames, filenames in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)
        if exists(dst_dir):
            _shdorc(copy, filenames, src_dir, dst_dir, overwrite)
        else:
            _shdo(copytree, src_dir, dst_dir, overwrite, dirnames)


def copy(src, dst, overwrite=None, preserve_metadata=True):
    if not os.path.isdir(dst) or not os.path.isdir(src):
        return _shdo(shutil.copytree, src, dst, overwrite)
    return _copyrc(src, dst, overwrite, preserve_metadata)


def exists(path, strict=False):
    """
    Case-sensitive os.path.exists.
    """
    if not strict:
        return os.path.exists(path)
    if os.path.exists(path):
        dirpath, name = os.path.split(path)
        return name in os.listdir(dirpath)
    else:
        return False


def filesize(filename):
    return os.stat(filename).st_size


def filetype(filename):
    try:
        return magic.from_file(filename, mime=True)
    except NameError:
        pass
    return guess_mime(filename)


def fullpath(path):
    return os.path.realpath(os.path.expanduser(path))


def blksize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    if os.name != 'nt':
        size = os.statvfs(path).f_bsize
    else:
        import ctypes
        drive = "{0}\\".format(os.path.splitdrive(os.path.abspath(path))[0])
        cluster_sectors = ctypes.c_longlong(0)
        sector_size = ctypes.c_longlong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(
            ctypes.c_wchar_p(drive), ctypes.pointer(cluster_sectors),
            ctypes.pointer(sector_size), None, None)
        size = int(cluster_sectors.value * sector_size.value)
    return size


def isexec(filename):
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


_open = open if sys.version_info > (2,) else io.open

@contextmanager
def open(filename, mode='r', buffering=-1, encoding='utf-8', errors=None,
         newline=None, closefd=True):
    if encoding is None:
        encoding = locale.getpreferredencoding(do_setlocale=False) or 'utf-8'
    with _open(filename, mode, buffering, encoding, errors, newline, closefd) as fp:
        yield fp


@contextmanager
def lopen(filename, mode='r', buffering=-1, encoding='utf-8', errors=None,
          newline=None, closefd=True, blocking=True):
    flags = portalocker.LOCK_EX if blocking else portalocker.LOCK_EX | portalocker.LOCK_NB
    with open(filename, mode, buffering, encoding, errors, newline, closefd) as fp:
        portalocker.lock(fp, flags)
        yield fp


def flush(filename, exist_ok=False):
    if not exist_ok and not os.path.exists(filename):
        raise OSError("Path not exists")
    with lopen(filename) as fp:
        fp.flush()
        os.fsync(fp.fileno())


def merge(dst_file, src_file):
    buf = blksize(src_file)
    with lopen(dst_file, mode='ab') as dfp:
        with lopen(src_file, mode='rb') as sfp:
            for chunk in iter(lambda: sfp.read(buf), b''):
                dfp.write(chunk)


def mountpoint(path):
    path = fullpath(path)
    rest = True
    while rest:
        if os.path.ismount(path):
            return path
        path, rest = path.rsplit(os.sep, 1)


def filesystem(path):
    mp = mountpoint(path)
    fs = dict((part.mountpoint, part.fstype) for part in psutil.disk_partitions())
    return fs.get(mp)


def mkfile(filename, size=None):
    if os.path.isfile(filename):
        raise OSError("Path already exists")
    with lopen(filename, mode='wb') as fp:
        if size and os.name == 'nt':
            fp.truncate(size)


def makedirs(dirname, mode=0o777, exist_ok=False):
    try:
        os.makedirs(dirname, mode)
    except OSError as e:
        if not os.path.isdir(dirname) or not exist_ok:
            raise OSError(e)


def makefile(filepath, mode=0o700, size=None, exist_ok=False):
    dirname, filename = os.path.split(filepath)
    makedirs(dirname, mode, exist_ok=True)
    try:
        mkfile(filename, size)
    except OSError as e:
        if not os.path.isfile(filepath) or not exist_ok:
            raise OSError(e)


def _moverc(src, dst, overwrite):
    exists = os.path.exists
    move = shutil.move
    removedirs = os.removedirs
    for src_dir, dirnames, filenames in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)
        if exists(dst_dir):
            _shdorc(move, filenames, src_dir, dst_dir, overwrite)
        else:
            _shdo(move, src_dir, dst_dir, overwrite, dirnames)
        try:
            removedirs(src_dir)
        except Exception:
            pass


def move(src, dst, overwrite=None):
    if not os.path.isdir(dst) or not os.path.isdir(src):
        return _shdo(shutil.move, src, dst, overwrite)
    _moverc(src, dst, overwrite)
    try:
        os.rmdir(src)
    except Exception:
        pass


def mtime(path):
    getmtime = os.path.getmtime
    join = os.path.join

    if not os.path.isdir(path):
        return getmtime(path)

    mtimes = [getmtime(join(dirpath, fname))
              for dirpath, dirnames, filenames in os.walk(path)
              for fname in filenames]

    return max(0, 0, *mtimes)


def _cleanpy2(dirpath, filenames):
    join = os.path.join
    remove = os.remove
    for fname in filenames:
        if fname[-4:] not in ('.pyc', '.pyo', '.pyd'):
            continue
        try:
            remove(join(dirpath, fname))
        except Exception:
            continue


def _cleanpy3(dirpath, dirnames):
    cname = '__pycache__'
    if cname not in dirnames:
        return None
    dirnames.remove(cname)
    try:
        os.remove(os.path.join(dirpath, cname))
    except Exception:
        pass


def cleanpy(dirname, recursive=True):
    walkpath = os.walk(dirname)
    if not recursive:
        walkpath = (next(walkpath))
    for dirpath, dirnames, filenames in walkpath:
        _cleanpy2(dirpath, filenames)
        _cleanpy3(dirpath, dirnames)


def remove(path, trash=False, ignore_errors=False):
    if not os.path.exists(path):
        if ignore_errors:
            return None
        raise OSError("Path not exists")
    if trash:
        send2trash.send2trash(path)
    elif os.path.isdir(path):
        shutil.rmtree(path, ignore_errors)
    elif os.path.isfile(path):
        os.remove(path)
    else:
        raise TypeError


def empty(path, trash=False, exist_ok=True):
    if not exist_ok and not os.path.exists(path):
        raise OSError("Path not exists")
    if os.path.isfile(path):
        if trash:
            origfile = path + '.orig'
            os.rename(path, origfile)
            shutil.copy2(origfile, path)
            remove(path, trash)
            os.rename(origfile, path)
        fp = open(path, mode='wb')
        fp.close()
    elif os.path.isdir(path):
        for name in os.listdir(path):
            remove(name, trash)
    else:
        raise TypeError


def which(filename):
    try:
        return shutil.which(filename)  # NOTE: Available only under Python 3
    except AttributeError:
        pass

    dirname = os.path.dirname(filename)
    if dirname:
        return filename if isexec(filename) else None

    for envpath in os.environ['PATH'].split(os.pathsep):
        filename = os.path.join(envpath.strip('"'), filename)
        if isexec(filename):
            return filename
