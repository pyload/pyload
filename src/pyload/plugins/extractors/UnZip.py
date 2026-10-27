import fnmatch
import os
import stat
import sys
import zipfile

from pyload.core.utils.convert import to_bytes
from pyload.core.utils.fs import safejoin
from pyload.plugins.base.extractor import ArchiveError, BaseExtractor, CRCError, PasswordError


class UnZip(BaseExtractor):
    __name__ = "UnZip"
    __type__ = "extractor"
    __version__ = "1.31"
    __status__ = "stable"

    __description__ = """ZIP extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    VERSION = "{}.{}.{}".format(
        sys.version_info[0], sys.version_info[1], sys.version_info[2]
    )

    @classmethod
    def archivetype(cls, filename):
        try:
            return "zip" if cls.isarchive(filename) else None

        except IOError:
            return None

    @classmethod
    def isarchive(cls, filename):
        if os.path.splitext(filename)[1].lower() != ".zip":
            return False

        #: zipfile only checks for 'End of archive' so we have to check ourselves for 'start of archive'
        try:
            with open(filename, "rb") as f:
                data = f.read(4)
                if data != b"PK\003\004":
                    return False

                else:
                    return zipfile.is_zipfile(f)

        except IOError:
            return False

    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 6)

    def init(self):
        self.smallest = None
        self.members = None

    def list(self, password=None):
        if not self.files:
            with zipfile.ZipFile(self.filename, "r") as z:
                if password:
                    z.setpassword(to_bytes(password))
                self.files = [
                    safejoin(self.dest, *_f.replace("\\", "/").rstrip("/").split("/"))
                    for _f in z.namelist()
                    if not _f.endswith("/")
                ]

        return self.files

    def verify_password(self, password=None):
        try:
            with zipfile.ZipFile(self.filename, "r") as z:
                if password:
                    z.setpassword(to_bytes(password))

                encrypted = self._check_archive_encryption(z)
                if encrypted:
                    if not password:
                        raise PasswordError("Archive is password protected")

                    # Verify password on the smallest file to avoid full archive decompression
                    smallest = self._find_smallest_file(z)[0]
                    if smallest is None:
                        raise ArchiveError("Cannot find smallest file")

                    # Verify password by reading a small portion of the smallest file
                    with z.open(smallest) as f:
                        f.read(1024)

        except (zipfile.BadZipfile, zipfile.LargeZipFile) as exc:
            raise ArchiveError(exc)

        except RuntimeError as exc:
            if "encrypted" in str(exc) or "Bad password" in str(exc):
                raise PasswordError(exc)
            else:
                raise CRCError(exc)

    def extract(self, password=None):
        try:
            with zipfile.ZipFile(self.filename, "r") as z:
                if password:
                    z.setpassword(to_bytes(password))

                # Validate file list BEFORE extraction to prevent path traversal
                namelist = z.namelist()
                self._validate_archive_entries(namelist)

                # Validate symlink targets BEFORE extraction
                self._validate_zip_symlinks(z)

                members = self._get_members(z)

                # Validate free space BEFORE extraction
                required_size = sum(
                    zip_info.file_size
                    for zip_info in z.infolist()
                    if zip_info.filename in members
                )
                self._check_free_space(required_size)

                z.extractall(self.dest, members=members)
                self.files = [
                    safejoin(
                        self.dest,
                        *_f.replace("\\", "/").rstrip("/").split("/"),
                    )
                    for _f in members
                ]

            return self.files

        except (zipfile.BadZipfile, zipfile.LargeZipFile) as exc:
            raise ArchiveError(exc)

        except RuntimeError as exc:
            if "encrypted" in str(exc) or "Bad password" in str(exc):
                raise PasswordError(exc)
            else:
                raise CRCError(exc)

    def _is_zip_symlink(self, zip_info):
        """Check if a ZipInfo entry is a symlink using external attributes."""
        # External attributes upper 16 bits contain Unix file mode
        # Symlink mode is S_IFLNK (0xA000)
        return (zip_info.external_attr >> 16) & stat.S_IFLNK == stat.S_IFLNK

    def _validate_zip_symlinks(self, z):
        """
        Validate symlink targets in ZIP before extraction.

        :param z: zipfile.ZipFile object
        :raises ArchiveError: If any symlink points outside destination
        """
        for zip_info in z.infolist():
            if self._is_zip_symlink(zip_info):
                # For symlinks, the file content is the target path
                symlink_target = z.read(zip_info.filename).decode(
                    "utf-8", errors="replace"
                )
                self._validate_symlink_target(
                    zip_info.filename, symlink_target, self.dest
                )

    def _check_archive_encryption(self, z):
        """Check if the ZIP archive is encrypted."""
        encrypted = any(
            zip_info.flag_bits & zipfile._MASK_ENCRYPTED
            for zip_info in z.infolist()
        )
        return encrypted

    def _find_smallest_file(self, z):
        if not self.smallest:
            members = self._get_members(z)
            smallest = (None, 0)
            for zip_info in z.infolist():
                if zip_info.filename in members:
                    if smallest[1] == 0 or  (smallest[1] > zip_info.file_size > 0):
                        smallest = (zip_info.filename, zip_info.file_size)

            self.smallest = smallest

        return self.smallest

    def _get_members(self, z):
        if not self.members:
            members = [
                member
                for member in z.namelist()
                if not any(
                    fnmatch.fnmatch(member, exclusion)
                    for exclusion in self.excludefiles
                )
                and not member.endswith("/")
            ]
            self.members = members

        return self.members
