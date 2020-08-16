# -*- coding: utf-8 -*-

import hashlib
import io
import os
import shutil

# import portalocker
# import psutil
from .convert import to_bytes, to_str

try:
    import send2trash
except ImportError:
    send2trash = None
try:
    import magic
except ImportError:
    magic = None
    from filetype import guess_mime
try:
    import zlib
except ImportError:
    zlib = None


def free_space(path):
    availspace = None

    if os.name == "nt":
        import ctypes

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes)
        )
        availspace = free_bytes.value

    else:
        s = os.statvfs(path)
        availspace = s.f_frsize * s.f_bavail

    return availspace


def _shdo(func, src, dst, overwrite=None, ref=None):
    mtime = os.path.getmtime
    try:
        if os.path.isfile(dst):
            if overwrite is None and mtime(src) <= mtime(dst):
                return
            elif not overwrite:
                return
            if os.name == "nt":
                os.remove(dst)
        func(src, dst)
        if isinstance(ref, list):
            del ref[:]
    except (IOError, OSError):
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
    """Case-sensitive os.path.exists."""
    if not strict:
        return os.path.exists(path)
    if os.path.exists(path):
        dirpath, name = os.path.split(path)
        return name in os.listdir(dirpath)
    return False


def filesize(filename):
    return os.stat(filename).st_size


def filetype(filename):
    try:
        return magic.from_file(filename, mime=True)
    except AttributeError:
        pass
    return guess_mime(filename)


def encode(path):
    try:
        return os.fsencode(path)
    except AttributeError:
        return to_bytes(path)


def decode(path):
    try:
        return os.fsdecode(path)
    except AttributeError:
        return to_str(path)


def fullpath(path):
    return os.path.realpath(os.path.expanduser(path))


def blksize(path):
    """Get optimal file system buffer size (in bytes) for I/O calls."""
    if os.name != "nt":
        size = os.statvfs(path).f_bsize
    else:
        import ctypes

        drive = os.path.splitdrive(os.path.abspath(path))[0] + "\\"
        cluster_sectors = ctypes.c_longlong(0)
        sector_size = ctypes.c_longlong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(
            ctypes.c_wchar_p(drive),
            ctypes.pointer(cluster_sectors),
            ctypes.pointer(sector_size),
            None,
            None,
        )
        size = int(cluster_sectors.value * sector_size.value)
    return size


def bufread(fp, buffering=-1, sentinel=b""):
    buf = blksize(fp.name) if buffering < 0 else buffering
    func = fp.readline if buffering == 1 else lambda: fp.read(buf)
    return iter(func, sentinel)


def _crcsum(filename, chkname, buffering):
    last = 0
    call = getattr(zlib, chkname)
    with io.open(filename, mode="rb") as fp:
        for chunk in bufread(fp, buffering):
            last = call(chunk, last)
    return f"{last & 0xffffffff:x}"


def _hashsum(filename, chkname, buffering):
    h = hashlib.new(chkname)
    buffering *= h.block_size
    with io.open(filename, mode="rb") as fp:
        for chunk in bufread(fp, buffering):
            h.update(chunk)
    return h.hexdigest()


def checksum(filename, chkname, buffering=None):
    res = None
    buf = buffering or blksize(filename)
    if chkname in ("adler32", "crc32"):
        res = _crcsum(filename, chkname, buf)
    elif chkname in hashlib.algorithms_available:
        res = _hashsum(filename, chkname, buf)
    return res


def is_exec(filename):
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


# def lopen(*args, **kwargs):
# if kwargs.get("blocking", True):
# flags = portalocker.LOCK_EX
# else:
# flags = portalocker.LOCK_EX | portalocker.LOCK_NB
# fp = io.open(*args, **kwargs)
# portalocker.lock(fp, flags)
# return fp


def flush(filename, exist_ok=False):
    if not exist_ok and not os.path.exists(filename):
        raise OSError("Path not exists")
    with io.open(filename) as fp:
        fp.flush()
        os.fsync(fp.fileno())


def merge(dst_file, src_file):
    with io.open(dst_file, mode="ab") as dfp:
        with io.open(src_file, mode="rb") as sfp:
            for chunk in bufread(sfp):
                dfp.write(chunk)


def mountpoint(path):
    path = fullpath(path)
    rest = True
    while rest:
        if os.path.ismount(path):
            return path
        path, rest = path.rsplit(os.sep, 1)


# def filesystem(path):
# mp = mountpoint(path)
# fs = dict((part.mountpoint, part.fstype) for part in psutil.disk_partitions())
# return fs.get(mp)


def mkfile(filename, size=None):
    if os.path.isfile(filename):
        raise OSError("Path already exists")
    with io.open(filename, mode="wb") as fp:
        if size and os.name == "nt":
            fp.truncate(size)


def makedirs(dirname, mode=0o777, exist_ok=False):
    try:
        os.makedirs(dirname, mode)

    except OSError as exc:
        if not os.path.isdir(dirname) or not exist_ok:
            raise OSError(exc)


def makefile(filepath, mode=0o700, size=None, exist_ok=False):
    dirname, _ = os.path.split(filepath)
    makedirs(dirname, mode, exist_ok=True)
    try:
        mkfile(filepath, size)

    except OSError as exc:
        if not os.path.isfile(filepath) or not exist_ok:
            raise OSError(exc)


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

    mtimes = (
        getmtime(join(root, fname))
        for root, dirnames, filenames in os.walk(path)
        for fname in filenames
    )

    return max(0, 0, *mtimes)


def _cleanpy2(root, filenames):
    join = os.path.join
    remove = os.remove
    for fname in filenames:
        if fname[-4:] not in (".pyc", ".pyo", ".pyd"):
            continue
        try:
            remove(join(root, fname))
        except OSError:
            pass


def _cleanpy3(root, dirnames):
    name = "__pycache__"
    if name not in dirnames:
        return
    dirnames.remove(name)
    try:
        os.remove(os.path.join(root, name))
    except OSError:
        pass


def cleanpy(dirname, recursive=True):
    walk_it = os.walk(dirname)
    if not recursive:
        walk_it = next(walk_it)
    for dirpath, dirnames, filenames in walk_it:
        _cleanpy2(dirpath, filenames)
        _cleanpy3(dirpath, dirnames)


def remove(path, try_trash=True):
    # path = os.fsdecode(path)

    if not os.path.exists(path):
        return

    if try_trash:
        try:
            send2trash.send2trash(path)
        except AttributeError as exc:
            exc_logger.exception(exc)

    elif os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)

    else:
        os.remove(path)


def empty(path, try_trash=False, exist_ok=True):
    if not exist_ok and not os.path.exists(path):
        raise OSError("Path not exists")

    if os.path.isfile(path):
        if try_trash:
            origfile = path + ".orig"
            os.rename(path, origfile)
            shutil.copy2(origfile, path)
            remove(path, try_trash)
            os.rename(origfile, path)
        fp = io.open(path, mode="wb")
        fp.close()

    elif os.path.isdir(path):
        for name in os.listdir(path):
            remove(name, try_trash)
    else:
        raise TypeError


def which(filename):
    try:
        return shutil.which(filename)  # NOTE: Available only under Python 3
    except AttributeError:
        pass

    dirname = os.path.dirname(filename)
    if dirname:
        return filename if is_exec(filename) else None

    for envpath in os.environ["PATH"].split(os.pathsep):
        filename = os.path.join(envpath.strip('"'), filename)
        if is_exec(filename):
            return filename
