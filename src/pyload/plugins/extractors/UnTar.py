import copy
import os
import sys
import tarfile

from pyload.core.utils.fs import is_within_directory, safejoin
from pyload.plugins.base.extractor import ArchiveError, BaseExtractor, CRCError


class UnTar(BaseExtractor):
    __name__ = "UnTar"
    __type__ = "extractor"
    __version__ = "0.10"
    __status__ = "stable"

    __description__ = """TAR extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    VERSION = "{}.{}.{}".format(
        sys.version_info[0], sys.version_info[1], sys.version_info[2]
    )

    @classmethod
    def archivetype(cls, filename):
        return "tar" if cls.isarchive(filename) else None

    @classmethod
    def isarchive(cls, filename):
        fsname = os.fsdecode(filename)
        try:
            if tarfile.is_tarfile(fsname):
                with tarfile.open(fsname) as tf:
                    return len(tf.getmembers()) > 0
            return False
        except IOError:
            return False

    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 5)

    def list(self, password=None):
        with tarfile.open(self.filename) as t:
            self.files = [safejoin(self.dest, _f) for _f in t.getnames()]
        return self.files

    def verify(self, password=None):
        try:
            t = tarfile.open(self.filename, errorlevel=1)

        except tarfile.CompressionError as exc:
            raise CRCError(exc)

        except (OSError, tarfile.TarError) as exc:
            raise ArchiveError(exc)

        else:
            t.close()

    def _safe_extractall(self, tar, path=".", members=None, *, numeric_owner=False):
        """
        Extract TAR members using data-filter rules on all supported Python versions.

        :param tar: tarfile.TarFile object
        :param path: Destination directory
        :param members: List of members to extract (None = all)
        :param numeric_owner: Whether to use numeric owner IDs
        """
        for member in tar.getmembers():
            member_path = os.path.join(path, member.name)
            if not is_within_directory(path, member_path):
                raise ArchiveError("Attempted Path Traversal in Tar File (CVE-2007-4559)")
            if member.isdev():
                raise ArchiveError("Device files are not allowed in TAR archives.")

        extraction_members = members if members is not None else tar.getmembers()

        def filtered_members():
            for member in extraction_members:
                yield self._filter_tar_member(member, path)

        tar.extractall(path, filtered_members(), numeric_owner=numeric_owner)

    @staticmethod
    def _filter_tar_member(member: tarfile.TarInfo, dest_path: str):
        """Apply the security rules of tarfile's ``data`` extraction filter."""
        filtered_member = copy.copy(member)
        dest_path = os.path.realpath(dest_path)

        name = member.name.lstrip("/" + os.sep)
        if name != member.name:
            filtered_member.name = name
        if os.path.isabs(name):
            raise ArchiveError("Absolute paths are not allowed in TAR archives.")

        target_path = os.path.realpath(os.path.join(dest_path, name))
        try:
            if not is_within_directory(dest_path, target_path):
                raise ArchiveError(
                    "Attempted Path Traversal in Tar File (CVE-2007-4559)"
                )
        except ValueError as exc:
            raise ArchiveError("Invalid path in TAR archive.") from exc

        mode = member.mode
        if mode is not None:
            mode &= 0o755
            if member.isreg() or member.islnk():
                if not mode & 0o100:
                    mode &= ~0o111
                mode |= 0o600
            elif member.isdir() or member.issym():
                mode = None
            else:
                raise ArchiveError("Special files are not allowed in TAR archives.")
            setattr(filtered_member, "mode", mode)

        for attribute in ("uid", "gid", "uname", "gname"):
            setattr(filtered_member, attribute, None)

        if member.issym() or member.islnk():
            linkname = member.linkname
            if os.path.isabs(linkname):
                raise ArchiveError(
                    f"Symlink '{member.name}' with absolute target: {linkname}"
                )
            linkname = os.path.normpath(linkname)
            filtered_member.linkname = linkname

            if member.issym():
                link_path = os.path.join(dest_path, os.path.dirname(name), linkname)
            else:
                link_path = os.path.join(dest_path, linkname)
            target_path = os.path.realpath(link_path)
            try:
                if not is_within_directory(dest_path, target_path):
                    raise ArchiveError(
                        f"Link '{member.name}' points outside the destination."
                    )
            except ValueError as exc:
                raise ArchiveError(
                    f"Invalid link target in TAR archive: {linkname}"
                ) from exc

        return filtered_member

    def extract(self, password=None):
        self.verify(password)

        try:
            with tarfile.open(self.filename, errorlevel=2) as t:
                # Validate file list BEFORE extraction to prevent path traversal
                members = t.getmembers()
                self._validate_archive_entries([m.name for m in members])

                self._safe_extractall(t, self.dest)
                self.files = t.getnames()
            return self.files

        except tarfile.ExtractError as exc:
            self.log_warning(exc)

        except tarfile.CompressionError as exc:
            raise CRCError(exc)

        except (OSError, tarfile.TarError) as exc:
            raise ArchiveError(exc)
