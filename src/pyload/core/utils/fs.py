import hashlib
import io
import os
import shutil

# import portalocker
# import psutil
from ... import exc_logger
from . import purge
from .convert import to_bytes, to_str

try:
    import send2trash
except ImportError:
    send2trash = None
try:
    import magic

    def guess_mime(filename):
        return magic.from_file(filename, mime=True)
except ImportError:
    from filetype import guess_mime
try:
    import zlib
except ImportError:
    zlib = None


def free_space(path):
    """
    Return the available free space (in bytes) for the filesystem containing path.

    Parameters:
    - path (str): A filesystem path to check free space for.

    Returns:
    - int: Number of free bytes available on the filesystem, or None on failure.
    """
    available_space = None

    if os.name == "nt":
        import ctypes

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes)
        )
        available_space = free_bytes.value

    else:
        s = os.statvfs(path)
        available_space = s.f_frsize * s.f_bavail

    return available_space


def _shdo(func, src, dst, overwrite=None, ref=None):
    """
    Helper to perform single-file or directory operation with optional overwrite logic.

    Parameters:
    - func (callable): Function to perform the operation (e.g., shutil.copytree, shutil.copy).
    - src (str): Source path.
    - dst (str): Destination path.
    - overwrite (bool|None): Overwrite behavior. If None, overwrite only if src is newer than dst.
      If False, do not overwrite. If True, always overwrite.
    - ref (list|None): If provided and is a list, it will be cleared on success (used to pass dirnames).

    Returns:
    - None
    """
    try:
        if os.path.isfile(dst):
            if overwrite is None and os.path.getmtime(src) <= os.path.getmtime(dst):
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
    """
    Helper to perform a per-file operation for all filenames in a source directory.

    Parameters:
    - func (callable): Function to perform on each file (e.g., shutil.copy).
    - filenames (iterable): Filenames (not full paths) in src_dir.
    - src_dir (str): Source directory path.
    - dst_dir (str): Destination directory path.
    - overwrite (bool|None): Overwrite behavior passed to _shdo.

    Returns:
    - None
    """
    for fname in filenames:
        src_file = os.path.join(src_dir, fname)
        dst_file = os.path.join(dst_dir, fname)
        _shdo(func, src_file, dst_file, overwrite)


def _copyrc(src, dst, overwrite, preserve_metadata):
    """
    Recursive copy implementation used when both src and dst are directories.

    Walks src tree and copies files/directories into dst. Uses metadata-preserving
    copy (copy2) when preserve_metadata is True, otherwise uses shutil.copy.

    Parameters:
    - src (str): Source directory path.
    - dst (str): Destination directory path.
    - overwrite (bool|None): Overwrite policy passed to helpers.
    - preserve_metadata (bool): Whether to preserve file metadata.

    Returns:
    - None
    """
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
    """
    Copy file or directory from src to dst.

    If both src and dst are directories, performs a recursive directory copy.
    Otherwise performs a single copy or copytree depending on the types.

    Parameters:
    - src (str): Source file or directory.
    - dst (str): Destination path.
    - overwrite (bool|None): Overwrite behavior. If None, overwrite only if src is newer.
    - preserve_metadata (bool): Preserve metadata when copying files.

    Returns:
    - None
    """
    if not os.path.isdir(dst) or not os.path.isdir(src):
        return _shdo(shutil.copytree, src, dst, overwrite)
    return _copyrc(src, dst, overwrite, preserve_metadata)


def exists(path, strict=False):
    """
    Check existence of a path with optional case-sensitive check.

    Parameters:
    - path (str): Path to check.
    - strict (bool): If True perform a case-sensitive existence check by listing
      the parent directory contents. Defaults to False.

    Returns:
    - bool: True if path exists (and matches case when strict=True), False otherwise.
    """
    if not strict:
        return os.path.exists(path)
    if os.path.exists(path):
        dirpath, name = os.path.split(path)
        return name in os.listdir(dirpath)
    return False


def filesize(filename):
    """
    Return the size of the file in bytes.

    Parameters:
    - filename (str): Path to the file.

    Returns:
    - int: File size in bytes.
    """
    return os.stat(filename).st_size


def filetype(filename):
    """
    Guess the MIME type of a file.

    Parameters:
    - filename (str): Path to the file.

    Returns:
    - str: MIME type string guessed for the file, or None if unknown.
    """
    return guess_mime(filename)


def encode(path):
    """
    Encode a filesystem path to bytes using os.fsencode or fallback conversion.

    Parameters:
    - path (str|bytes): Path to encode.

    Returns:
    - bytes: Encoded filesystem path.
    """
    try:
        return os.fsencode(path)
    except AttributeError:
        return to_bytes(path)


def decode(path):
    """
    Decode a filesystem path from bytes to str using os.fsdecode or fallback.

    Parameters:
    - path (bytes|str): Path to decode.

    Returns:
    - str: Decoded filesystem path.
    """
    try:
        return os.fsdecode(path)
    except AttributeError:
        return to_str(path)


def fullpath(path):
    """
    Expand user tilde and resolve symbolic links to return the absolute real path.

    Parameters:
    - path (str): Path to normalize.

    Returns:
    - str: Normalized absolute path.
    """
    return os.path.realpath(os.path.expanduser(path))


def blksize(path):
    """
    Get the optimal filesystem block size (buffer size) for I/O on the given path.

    Parameters:
    - path (str): Path on the filesystem to query.

    Returns:
    - int: Preferred block size in bytes.
    """
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
    """
    Return an iterator that yields chunks from file-like object `fp`.

    If buffering < 0 the function uses the filesystem block size for fp.name.
    If buffering == 1 it yields lines (fp.readline). Otherwise, it yields
    fixed-size chunks using fp.read(buf).

    Parameters:
    - fp (file-like): Open file object with .read/.readline and .name attributes.
    - buffering (int): Buffer policy: -1 (auto), 1 (line-by-line), >1 chunk size.
    - sentinel (bytes): When iterator yields this sentinel value iteration stops.

    Returns:
    - iterator: Iterator that yields data chunks until sentinel is returned.
    """
    buf = blksize(fp.name) if buffering < 0 else buffering
    func = fp.readline if buffering == 1 else lambda: fp.read(buf)
    return iter(func, sentinel)


def _crcsum(filename, chkname, buffering):
    """
    Compute a CRC-style checksum (adler32 or crc32) for a file.

    Parameters:
    - filename (str): Path to the file.
    - chkname (str): Name of zlib checksum function ('adler32' or 'crc32').
    - buffering (int): Buffer size used for reading chunks.

    Returns:
    - str: Hex string of the computed checksum.
    """
    last = 0
    call = getattr(zlib, chkname)
    with io.open(filename, mode="rb") as fp:
        for chunk in bufread(fp, buffering):
            last = call(chunk, last)
    return f"{last & 0xffffffff:x}"


def _hashsum(filename, chkname, buffering):
    """
    Compute a cryptographic hash for a file using hashlib.

    Parameters:
    - filename (str): Path to the file.
    - chkname (str): Name of the hashing algorithm (e.g., 'sha1', 'md5').
    - buffering (int): Number of blocks to read multiplied by the hash block size.

    Returns:
    - str: Hex digest of the file hash.
    """
    h = hashlib.new(chkname)
    buffering *= h.block_size
    with io.open(filename, mode="rb") as fp:
        for chunk in bufread(fp, buffering):
            h.update(chunk)
    return h.hexdigest()


def checksum(filename, chkname, buffering=None):
    """
    Compute a checksum or digest for a file.

    Supports 'adler32' and 'crc32' via zlib, or any algorithm available in
    hashlib.algorithms_available.

    Parameters:
    - filename (str): Path to the file.
    - chkname (str): Checksum or algorithm name.
    - buffering (int|None): Buffer size in bytes to use while reading. If None,
      the filesystem block size is used.

    Returns:
    - str|None: Hex string of the computed checksum/digest, or None if chkname is unsupported.
    """
    res = None
    buf = buffering or blksize(filename)
    if chkname in ("adler32", "crc32"):
        res = _crcsum(filename, chkname, buf)
    elif chkname in hashlib.algorithms_available:
        res = _hashsum(filename, chkname, buf)
    return res


def is_exec(filename):
    """
    Check whether a file exists and is executable.

    Parameters:
    - filename (str): Path to the file.

    Returns:
    - bool: True if the file exists and has execute permissions, False otherwise.
    """
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
    """
    Flush and sync an open file to disk.

    Parameters:
    - filename (str): Path to an existing file to flush.
    - exist_ok (bool): If False and the file doesn't exist, raise OSError.
    """
    if not exist_ok and not os.path.exists(filename):
        raise OSError("Path not exists")
    with io.open(filename) as fp:
        fp.flush()
        os.fsync(fp.fileno())


def merge(dst_file, src_file):
    """
    Append the contents of src_file to dst_file.

    Parameters:
    - dst_file (str): Destination file path opened in append-binary mode.
    - src_file (str): Source file path to read from.
    """
    with io.open(dst_file, mode="ab") as dfp:
        with io.open(src_file, mode="rb") as sfp:
            for chunk in bufread(sfp):
                dfp.write(chunk)


def mountpoint(path):
    """
    Return the mount point for the given path.

    Parameters:
    - path (str): Filesystem path.

    Returns:
    - str: Mount point path that contains the provided path.
    """
    path = fullpath(path)
    rest = True
    while rest:
        if os.path.ismount(path):
            return path
        path, rest = path.rsplit(os.sep, 1)

    return None


# def filesystem(path):
# mp = mountpoint(path)
# fs = dict((part.mountpoint, part.fstype) for part in psutil.disk_partitions())
# return fs.get(mp)


def mkfile(filename, size=None):
    """
    Create an empty file at filename. Optionally set its size on Windows.

    Parameters:
    - filename (str): Path to create.
    - size (int|None): Size in bytes to preallocate on creation (Windows only).

    Raises:
    - OSError: If the path already exists.
    """
    if os.path.isfile(filename):
        raise OSError("Path already exists")
    with io.open(filename, mode="wb") as fp:
        if size and os.name == "nt":
            fp.truncate(size)


def makedirs(dirname, mode=0o777, exist_ok=False):
    """
    Create directories recursively.

    Parameters:
    - dirname (str): Directory path to create.
    - mode (int): Permissions mode passed to os.makedirs.
    - exist_ok (bool): If True, do not raise if the directory already exists.
    """
    try:
        os.makedirs(dirname, mode)

    except OSError as exc:
        if not os.path.isdir(dirname) or not exist_ok:
            raise OSError(exc)


def makefile(filepath, mode=0o700, size=None, exist_ok=False):
    """
    Ensure parent directories exist and create a file.

    Parameters:
    - filepath (str): Path of the file to create.
    - mode (int): Mode for created directories.
    - size (int|None): Optional size to allocate (passed to mkfile).
    - exist_ok (bool): If True, do not raise if file already exists.
    """
    dirname, _ = os.path.split(filepath)
    makedirs(dirname, mode, exist_ok=True)
    try:
        mkfile(filepath, size)

    except OSError as exc:
        if not os.path.isfile(filepath) or not exist_ok:
            raise OSError(exc)


def _moverc(src, dst, overwrite):
    """
    Recursive move helper used when moving directory trees.

    Walks the src directory tree and moves contents into dst using shutil.move,
    handling existing destination directories according to overwrite policy.
    """
    removedirs = os.removedirs
    for src_dir, dirnames, filenames in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)
        if os.path.exists(dst_dir):
            _shdorc(shutil.move, filenames, src_dir, dst_dir, overwrite)
        else:
            _shdo(shutil.move, src_dir, dst_dir, overwrite, dirnames)
        try:
            removedirs(src_dir)
        except Exception:
            pass


def move(src, dst, overwrite=None):
    """
    Move a file or directory from src to dst.

    If both src and dst are directories performs a recursive move, otherwise
    uses shutil.move for single paths.

    Parameters:
    - src (str): Source path.
    - dst (str): Destination path.
    - overwrite (bool|None): Overwrite behavior passed to helpers.
    """
    if not os.path.isdir(dst) or not os.path.isdir(src):
        return _shdo(shutil.move, src, dst, overwrite)
    _moverc(src, dst, overwrite)
    try:
        os.rmdir(src)
    except Exception:
        pass


def mtime(path):
    """
    Return the modification time for a file, or if path is a directory the most recent modification time
    for files inside the directory.

    Parameters:
    - path (str): Path to a file or directory.

    Returns:
    - float: Latest modification time (seconds since epoch) among relevant files.
    """
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
    """
    Remove Python 2-style compiled files (.pyc, .pyo, .pyd) from a directory.

    Parameters:
    - root (str): Directory path.
    - filenames (iterable): Filenames in the directory to consider.
    """
    for fname in filenames:
        if fname[-4:] not in (".pyc", ".pyo", ".pyd"):
            continue
        try:
            os.remove(os.path.join(root, fname))
        except OSError:
            pass


def _cleanpy3(root, dirnames):
    """
    Remove __pycache__ directory remnants if present when cleaning Python files.

    Parameters:
    - root (str): Directory path.
    - dirnames (list): Directory names in the root; the function will remove
      "__pycache__" from the list to avoid descending into it and will attempt
      to remove the directory file if exists.
    """
    name = "__pycache__"
    if name not in dirnames:
        return
    dirnames.remove(name)
    try:
        os.remove(os.path.join(root, name))
    except OSError:
        pass


def cleanpy(dirname, recursive=True):
    """
    Remove compiled Python artifacts from a directory tree.

    Parameters:
    - dirname (str): Directory to clean.
    - recursive (bool): If True walk directories recursively; if False clean only
      the top-level directory.
    """
    walk_it = os.walk(dirname)
    if not recursive:
        walk_it = next(walk_it)
    for dirpath, dirnames, filenames in walk_it:
        _cleanpy2(dirpath, filenames)
        _cleanpy3(dirpath, dirnames)


def remove(path, try_trash=True):
    """
    Remove a filesystem path, attempting to move to trash first if available.

    Parameters:
    - path (str): Path to file or directory to remove.
    - try_trash (bool): If True attempt to send to trash using send2trash; on failure fall back to deletion.

    Returns:
    - None
    """
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
    """
    Empty a file or directory.

    If path is a file it truncates the file to zero length (or safely recreates
    it when try_trash=True). If path is a directory it removes its contents.
    If the path does not exist and exist_ok is False an OSError is raised.

    Parameters:
    - path (str): Path to file or directory to empty.
    - try_trash (bool): If True attempt a safe remove via trash before truncation.
    - exist_ok (bool): If False raise OSError when path does not exist.
    """
    if not exist_ok and not os.path.exists(path):
        raise OSError("Path not exists")

    if os.path.isfile(path):
        if try_trash:
            orig_file = path + ".orig"
            os.rename(path, orig_file)
            shutil.copy2(orig_file, path)
            remove(path, try_trash)
            os.rename(orig_file, path)
        fp = io.open(path, mode="wb")
        fp.close()

    elif os.path.isdir(path):
        for name in os.listdir(path):
            remove(name, try_trash)
    else:
        raise TypeError


def which(filename):
    """
    Locate an executable in PATH or return the filename if it is a path to an executable.

    Parameters:
    - filename (str): Program name or path.

    Returns:
    - str|None: Full path to executable if found, otherwise None.
    """
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


def is_within_directory(base_dir, target_dir):
    """
    Determine whether target_dir is located inside base_dir.

    Normalizes paths using realpath to account for symlinks and traversal
    sequences.

    Parameters:
    - base_dir (str): Base directory path.
    - target_dir (str): Target directory path to test.

    Returns:
    - bool: True if target_dir is within base_dir, False otherwise.
    """
    real_base = os.path.realpath(base_dir)
    real_target = os.path.realpath(target_dir)
    return os.path.commonpath([real_base, real_target]) == real_base


def safepath(value):
    """
    Sanitize a filesystem path by removing invalid characters and truncating long paths on Windows.

    Parameters:
    - value (str): Input path to sanitize.

    Returns:
    - str: Sanitized path safe to use on the local filesystem.
    """
    path_sep = os.sep if os.path.isabs(value) else ""
    drive, filename = os.path.splitdrive(value)

    fileparts = (safename(name) for name in filename.split(os.sep))

    filename = os.path.join(path_sep, *fileparts)
    path = drive + filename

    try:
        if os.name != "nt":
            return

        excess_chars = len(path) - 259
        if excess_chars < 1:
            return

        dirname, basename = os.path.split(filename)
        name, ext = os.path.splitext(basename)
        path = drive + os.path.join(dirname, purge.truncate(name, len(name) - excess_chars)) + ext

    finally:
        return path


def safejoin(*args):
    """
    Join path components and return a sanitized path ensuring no path traversal.

    The first argument is treated as the base directory and the returned path
    is validated to be within that base.

    Parameters:
    - *args (str): Path components to join (first must be the base directory).

    Returns:
    - str: Sanitized joined path.

    Raises:
    - ValueError: If less than one argument is provided or if path traversal is detected.
    """
    if len(args) < 1:
        raise ValueError("At least one argument required (base directory)")

    base = args[0]
    safe_joined = safepath(os.path.join(*args))

    if not is_within_directory(base, safe_joined):
        raise ValueError("Path traversal attempt detected")

    return safe_joined


def safename(value):
    """
    Remove invalid characters.
    """
    # badchars = '<>:"/\\|?*' if os.name == "nt" else '\0/\\"'
    badchars = '<>:"/\\|?*\0'
    name = purge.chars(value, badchars)
    return name
