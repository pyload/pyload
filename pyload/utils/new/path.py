# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

import codecs
import ctypes
import os
import shutil

import send2trash

from os.path import *

from pyload.utils.new import format
from pyload.utils.new.check import isiterable


@iterate
def availspace(folder):
    if os.name != "nt":
        stat = os.statvfs(folder)
        res = stat.f_frsize * stat.f_bavail
    else:
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder),
                                                   None,
                                                   None,
                                                   ctypes.pointer(free_bytes))
        res = int(free_bytes.value)
    return res


def copytree(src, dst, overwrite=None, preserve_metadata=True):
    NT = os.name == 'nt'
    copy = shutil.copy2 if preserve_metadata else shutil.copy
    copytree = shutil.copytree
    # isdir    = os.path.isdir
    # isfile   = os.path.isfile
    # join     = os.path.join
    mtime = os.path.getmtime
    remove = os.remove

    if not isdir(dst) or not isdir(src):
        return copytree(src, dst)

    for src_dir, dirnames, filenames in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)

        if not isdir(dst_dir):
            try:
                copytree(src_dir, dst_dir)
            except Exception:
                pass
            else:
                del dirnames[:]
            continue

        for filename in filenames:
            src_file = join(src_dir, filename)
            dst_file = join(dst_dir, filename)
            try:
                if isfile(dst_file):
                    if overwrite is None and mtime(src_file) <= mtime(dst_file):
                        continue
                    elif not overwrite:
                        continue
                    elif NT:
                        remove(dst_file)

                copy(src_file, dst_file)

            except Exception:
                continue


@iterate
def exists(path, case_sensitive=False):
    """
    Case-sensitive os.path.exists.
    """
    if not case_sensitive:
        return os.path.exists(path)
    if os.path.exists(path):
        dir, name = os.path.split(path)
        return name in os.listdir(dir)
    else:
        return False


@iterate
def filesize(path):
    return os.stat(path).st_size


def open(path, *args, **kwargs):
    return codecs.open(format.path(path), *args, **kwargs)


def flush(path):
    if not exists(path):
        return
    if isfile(path):
        with open(path) as f:
            f.flush()
        os.fsync(f.fileno())
    elif isdir(path):
        remove(os.listdir(path), trash=False)
    else:
        raise TypeError(path)


@iterate
def fsbsize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    if os.name != "nt":
        res = os.statvfs(path).f_bsize
    else:
        drive = "{}\\".format(splitdrive(abspath(path))[0])
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
    return isfile(path) and os.access(path, os.X_OK)


def merge(dstfile, srcfile):
    buf = fsbsize(srcfile)
    with open(dstfile, 'ab') as df:
        with open(srcfile, 'rb') as sf:
            for chunk in iter(lambda: sf.read(buf), b''):
                df.write(chunk)


def mkfile(path, opened=None):
    if exists(path):
        raise FileExistsError(path)
    mode = 'wb'
    f = open(path, mode)
    if not opened:
        f.close()
    elif opened != mode:
        f.close()
        f = open(path, opened)
    return f


def makedirs(path, mode=0o700, exist_ok=True):
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if not exist_ok or not isdir(name):
            raise OSError(e)


def makefile(path, opened=None, dirmode=0o700):
    dirname, basename = os.path.split(path)
    try:
        os.makedirs(dirname, dirmode)
    except OSError:
        pass
    return mkfile(basename, opened)


def movetree(src, dst, overwrite=None):
    NT = os.name == 'nt'
    # isdir      = os.path.isdir
    # isfile     = os.path.isfile
    # join       = os.path.join
    move = shutil.move
    mtime = os.path.getmtime
    remove = os.remove
    removedirs = os.removedirs

    if not isdir(dst) or not isdir(src):
        return move(src, dst)

    for src_dir, dirnames, filenames in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)

        if not isdir(dst_dir):
            try:
                move(src_dir, dst_dir)
            except Exception:
                pass
            else:
                del dirnames[:]
            continue

        for filename in filenames:
            src_file = join(src_dir, filename)
            dst_file = join(dst_dir, filename)
            try:
                if isfile(dst_file):
                    if overwrite is None and mtime(src_file) <= mtime(dst_file):
                        continue
                    elif not overwrite:
                        continue
                    elif NT:
                        remove(dst_file)

                move(src_file, dst_file)

            except Exception:
                continue
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
    # getmtime = os.path.getmtime
    # join     = os.path.join

    if not isdir(path):
        return getmtime(path)

    mtimes = [getmtime(join(dirpath, file))
              for dirpath, dirnames, filenames in os.walk(path)
              for file in filenames]

    return max(0, 0, *mtimes)


def remove(path, trash=True, ignore_errors=False):
    if not exists(path):
        return
    if trash:
        send2trash.send2trash(path)
    elif isdir(path):
        shutil.rmtree(path, ignore_errors)
    elif isfile(path):
        os.remove(path)
    else:
        raise TypeError(path)


@iterate
def which(name):
    # return shutil.which(command)  #@NOTE: Available under Python 3 only
    dirname, basename = split(name)
    if dirname:
        return name if isexec(name) else None

    for envpath in os.environ['PATH'].split(os.pathsep):
        filepath = join(envpath.strip('"'), name)
        if isexec(filepath):
            return filepath
