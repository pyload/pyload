import ntpath
import os
import re

from pyload.core.utils.fs import is_within_directory

from .plugin import BasePlugin


class ArchiveError(Exception):
    """
    raised when Archive error.
    """


class CRCError(Exception):
    """
    raised when CRC error.
    """


class PasswordError(Exception):
    """
    raised when password error.
    """


class BaseExtractor(BasePlugin):
    __name__ = "BaseExtractor"
    __type__ = "base"
    __version__ = "0.50"
    __status__ = "stable"

    __description__ = """Base extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Immenz", "immenz@gmx.net"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    EXTENSIONS = []
    REPAIR = False
    VERSION = None

    _RE_PART = re.compile(r"")

    @classmethod
    def archivetype(cls, filename):
        """
        Get archive default extension from filename

        :param filename: file name to test
        :return: Extension or None
        """
        name = os.path.basename(filename).lower()
        for ext in cls.EXTENSIONS:
            if isinstance(ext, str):
                if name.endswith("." + ext):
                    return ext

            elif isinstance(ext, tuple):
                if re.search(r"\." + ext[1] + "$", name):
                    return ext[0]
        return None

    @classmethod
    def isarchive(cls, filename):
        name = os.path.basename(filename).lower()
        for ext in cls.EXTENSIONS:
            if isinstance(ext, str):
                if name.endswith("." + ext):
                    return True

            elif isinstance(ext, tuple):
                if re.search(r"\." + ext[1] + "$", name):
                    return True

        return False

    @classmethod
    def ismultipart(cls, filename):
        return False

    @classmethod
    def find(cls):
        """
        Check if system statisfy dependencies
        """
        pass

    @classmethod
    def get_targets(cls, files_ids):
        """
        Filter suited targets from list of filename id tuple list

        :param files_ids: List of filepathes
        :return: List of targets, id tuple list
        """
        targets = []
        processed = []

        for id, fname, fout in files_ids:
            if not cls.isarchive(fname):
                continue

            if cls.ismultipart(fname):
                pname = cls._RE_PART.sub("", fname)
            else:
                pname = os.path.splitext(fname)[0]

            if pname in processed:
                continue

            processed.append(pname)
            targets.append((id, fname, fout))

        return targets

    def __init__(
        self,
        pyfile,
        filename,
        out,
        fullpath=True,
        overwrite=False,
        excludefiles=None,
        priority=0,
        keepbroken=False,
    ):
        """
        Initialize extractor for specific file
        """
        self._init(pyfile.m.pyload)

        self.pyfile = pyfile
        self.filename = filename
        self.name = os.path.basename(filename)
        self.out = out
        self.fullpath = fullpath
        self.overwrite = overwrite
        self.excludefiles = excludefiles or []
        self.priority = priority
        self.keepbroken = keepbroken
        self.files = None

        self.init()

    @property
    def target(self):
        return os.fsdecode(self.filename)

    @property
    def dest(self):
        return os.fsdecode(self.out)

    def verify(self, password=None):
        """
        Testing with Extractors built-in method Raise error if password is needed,
        integrity is questionable or else
        """
        pass

    def repair(self):
        pass

    def extract(self, password=None):
        """
        Extract the archive Raise specific errors in case of failure
        """
        raise NotImplementedError

    def chunks(self):
        """
        Return list of archive parts
        """
        return [self.filename]

    def list(self, password=None):
        """
        Return list of archive files
        """
        raise NotImplementedError

    def progress(self, x):
        """
        Set extraction progress
        """
        return self.pyfile.set_progress(int(x))

    def _validate_archive_entries(self, file_list):
        """
        Validate that all archive entries are within the destination directory.
        Prevents Zip Slip / path traversal attacks.

        :param file_list: List of file paths from archive
        :return: List of validated file paths, raises ArchiveError if paths are unsafe
        """
        validated = []
        for entry in file_list:
            if not entry:
                raise ArchiveError("Invalid archive entry: empty path")

            if isinstance(entry, bytes):
                # Normalize the entry path
                entry = os.fsdecode(entry)

            # Reject null bytes
            if "\x00" in entry:
                raise ArchiveError(f"Archive entry contains Null: {entry}")

            # Reject if entry includes a drive letter
            drive = ntpath.splitdrive(entry)[0]
            if drive:
                raise ArchiveError(f"Attempted path traversal in archive: {entry}")

            # Normalize all separators to forward slashes first
            normalized = entry.replace("\\", "/")

            # Reject absolute paths (also catches UNC paths)
            if normalized.startswith("/"):
                raise ArchiveError(f"Attempted path traversal in archive: {entry}")

            # Check for invalid Windows characters
            invalid_chars = '<>:"|?*'
            for char in invalid_chars:
                if char in normalized:
                    raise ArchiveError(f"Archive entry contains illegal character '{char}': {entry}")

            # Split and check for traversal
            parts = [part for part in normalized.split('/')]

            # Check for directory traversal
            level = 0
            for i, part in enumerate(parts):
                is_last = i == len(parts) - 1
                if part == '..':
                    level -= 1
                elif part == '' and not is_last:
                    raise ArchiveError(f"Invalid archive entry: {entry}")
                elif part not in ('', '.'):
                    level += 1
                if level < 0:
                    raise ArchiveError(f"Attempted path traversal in archive: {entry}")

            # Construct full extraction path
            full_path = os.path.realpath(os.path.join(self.dest, normalized))

            # Verify the file would be extracted within destination
            try:
                if not is_within_directory(self.dest, full_path):
                    raise ArchiveError(
                        f"Attempted path traversal in archive: {entry}"
                    )
            except ValueError:
                # is_within_directory can raise ValueError for invalid paths
                raise ArchiveError(
                    f"Invalid path in archive: {entry}"
                )

            validated.append(normalized)

        return validated

    def _validate_symlink_target(self, symlink_path, target, dest_dir):
        """
        Validate that a symlink's target resolves within the destination directory.
        Prevents symlink escape attacks.

        :param symlink_path: Path to the symlink entry in the archive
        :param target: Target path the symlink points to
        :param dest_dir: Destination extraction directory
        :return: True if valid, raises ArchiveError if unsafe
        """
        # Normalize the target
        target = os.fsdecode(target) if isinstance(target, bytes) else target

        # Reject absolute symlink targets
        if os.path.isabs(target):
            raise ArchiveError(
                f"Symlink '{symlink_path}' with absolute target: {target}"
            )

        # Reject targets with drive letters (Windows)
        if len(target) >= 2 and target[1] == ':':
            raise ArchiveError(
                f"Symlink '{symlink_path}' with invalid target: {target}"
            )

        # Construct the symlink location
        symlink_location = os.path.normpath(os.path.join(dest_dir, symlink_path))

        # Resolve the symlink target relative to its location
        symlink_dir = os.path.dirname(symlink_location)
        resolved_target = os.path.normpath(os.path.join(symlink_dir, target))

        # Verify the resolved target is within destination
        try:
            if not is_within_directory(dest_dir, resolved_target):
                raise ArchiveError(
                    f"Symlink '{symlink_path}' points outside destination: {target}"
                )
        except ValueError:
            raise ArchiveError(
                f"Symlink '{symlink_path}' has invalid target: {target}"
            )

        return True

    def _validate_extracted_symlinks(self):
        """
        Check extracted files for symlinks and validate their targets.
        Removes malicious symlinks that point outside the destination directory.
        Allows safe symlinks that point within the destination.
        Called after extraction as a paranoid safety check.
        """
        for root, dirs, files in os.walk(self.dest):
            # Check both files and directories (dirs might include symlink-to-dirs)
            for name in files + dirs:
                path = os.path.join(root, name)

                # Skip if not a symlink
                if not os.path.islink(path):
                    continue

                # Read the symlink target
                try:
                    target = os.readlink(path)
                except (OSError, ValueError):
                    # If we can't read it, remove it to be safe
                    try:
                        os.unlink(path)
                    except OSError:
                        pass
                    continue

                # Get the symlink's relative path in the destination
                symlink_rel_path = os.path.relpath(path, self.dest)

                # Validate the symlink target
                try:
                    self._validate_symlink_target(symlink_rel_path, target, self.dest)
                except ArchiveError:
                    # Remove the malicious symlink
                    try:
                        os.unlink(path)
                        self.log_warning(f"Removed malicious symlink: {symlink_rel_path}")
                    except OSError:
                        pass
                    # Re-raise to alert about the attack attempt
                    raise

