import os
import re
import subprocess

from pyload import PKGDIR
from pyload.core.utils.convert import to_str
from pyload.core.utils.fs import safejoin
from pyload.plugins.base.extractor import ArchiveError, BaseExtractor, CRCError, PasswordError
from pyload.plugins.helpers import renice


class SevenZip(BaseExtractor):
    __name__ = "SevenZip"
    __type__ = "extractor"
    __version__ = "0.41"
    __status__ = "testing"

    __description__ = """7-Zip extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Michael Nowak", None),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")
    ]

    CMD = "7z"
    EXTENSIONS = [
        ("7z", r"7z(?:\.\d{3})?"),
        "xz",
        "gz",
        "gzip",
        "tgz",
        "bz2",
        "bzip2",
        "tbz2",
        "tbz",
        "tar",
        "wim",
        "swm",
        "lzma",
        "rar",
        "cab",
        "arj",
        "z",
        "taz",
        "cpio",
        "rpm",
        "deb",
        "lzh",
        "lha",
        "chm",
        "chw",
        "hxs",
        "iso",
        "msi",
        "doc",
        "xls",
        "ppt",
        "dmg",
        "xar",
        "hfs",
        "exe",
        "ntfs",
        "fat",
        "vhd",
        "mbr",
        "squashfs",
        "cramfs",
        "scap",
    ]

    _RE_PART = re.compile(r"\.7z\.\d{3}|\.(part|r)\d+(\.rar|\.rev)?(\.bad)?|\.rar$", re.I)
    _RE_FILES = re.compile(
        r"([\d\-]+)\s+([\d:]+)\s+([RHSA.]+)\s+(\d+)\s+(?:(\d+)\s+)?(.+)"
    )
    _RE_ENCRYPTED_HEADER = re.compile(r"encrypted archive")
    _RE_ENCRYPTED_FILES = re.compile(r"Encrypted\s+=\s+\+")
    _RE_BADPWD = re.compile(r"Wrong password", re.I)
    _RE_BADCRC = re.compile(r"CRC Failed|Can not open file", re.I)
    _RE_VERSION = re.compile(
        r"7-Zip\s(?:\(\w+\)\s)?(?:\[(?:32|64)\]\s)?(\d+\.\d+)", re.I
    )

    @classmethod
    def find(cls):
        try:
            if os.name == "nt":
                cls.CMD = safejoin(PKGDIR, "lib", "7z.exe")

            p = subprocess.Popen(
                [cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
            )
            out, err = (r.strip() if r else "" for r in p.communicate())

        except OSError:
            return False

        else:
            m = cls._RE_VERSION.search(out)
            if m is not None:
                cls.VERSION = m.group(1)

            return True

    @classmethod
    def ismultipart(cls, filename):
        return cls._RE_PART.search(filename) is not None

    def init(self):
        self.smallest = None
        self.archive_encryption = None
        self.archive_info = []

    def verify(self, password=None):
        # First we check if the header (file list) is protected
        # if the header is protected, we can verify the password very fast without hassle.
        # otherwise, we find the smallest file in the archive and then try to extract it

        encrypted_header, encrypted_files = self._check_archive_encryption()
        if encrypted_header:
            self._get_archive_info(password)

        elif encrypted_files:
            #: search for smallest file and try to extract it to verify password
            smallest = self._find_smallest_file(password=password)[0]
            if smallest is None:
                raise ArchiveError("Cannot find smallest file")

            try:
                extracted = safejoin(self.dest, smallest if self.fullpath else os.path.basename(smallest))
                try:
                    os.remove(extracted)
                except OSError:
                    pass
                self.extract(password=password, file=smallest)

                #: Extraction was successful so exclude the file from further extraction
                if smallest not in self.excludefiles:
                    self.excludefiles.append(smallest)

            except (PasswordError, CRCError, ArchiveError) as exc:
                try:
                    os.remove(extracted)
                except (OSError, NameError):
                    pass

                raise exc

    def progress(self, process):
        s = ""
        while True:
            c = process.stdout.read(1)
            #: Quit loop on eof
            if not c:
                break
            #: Reading a percentage sign -> set progress and restart
            if c == '%' and s:
                self.pyfile.set_progress(int(s))
                s = ""
            #: Not reading a digit -> therefore restart
            elif not c.isdigit():
                s = ""
            #: Add digit to progress string
            else:
                s += c

    def extract(self, password=None, file=None):
        command = "x" if self.fullpath else "e"

        # Validate file list BEFORE extraction to prevent path traversal
        archive_info = self._get_archive_info(password)
        file_list = [entry["path"] for entry in archive_info]
        if file_list:
            self._validate_archive_entries(file_list)

        # Detect symlinks BEFORE extraction
        self._detect_7zip_symlinks(password)

        # Now do actual extraction
        p = self.call_cmd(command, "-o" + self.dest, self.filename, file, password=password)

        #: Communicate and retrieve stderr
        self.progress(p)
        out, err = (r.strip() if r else "" for r in p.communicate())

        if err:
            if self._RE_BADPWD.search(err):
                raise PasswordError

            elif self._RE_BADCRC.search(err):
                raise CRCError(err)

            else:  #: Raise error if anything is on stderr
                raise ArchiveError(err)

        if p.returncode > 1:
            raise ArchiveError(self._("Process return code: {}").format(p.returncode))

        # Post-extraction paranoid check: validate any symlinks that were created
        self._validate_extracted_symlinks()

        return self.list(password)

    def chunks(self):
        files = []
        dir, name = os.path.split(self.filename)

        #: eventually multi-part files
        files.extend(
            safejoin(dir, os.path.basename(_f))
            for _f in filter(self.ismultipart, os.listdir(dir))
            if self._RE_PART.sub("", name) == self._RE_PART.sub("", _f)
        )

        #: Actually extracted file
        if self.filename not in files:
            files.append(self.filename)

        return files

    def list(self, password=None):
        if not self.files:
            self._get_archive_info(password)
            self.files = [entry["full_path"] for entry in self.archive_info]

        return self.files

    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        #: Use UTF8 for console encoding
        args.append("-scsUTF-8")
        args.append("-sccUTF-8")

        #: Progress output
        if self.VERSION and float(self.VERSION) >= 15.08:
            #: Disable all output except progress and errors
            args.append("-bso0")
            args.append("-bsp1")

        #: Overwrite flag
        if self.overwrite:
            if self.VERSION and float(self.VERSION) >= 15.08:
                args.append("-aoa")

            else:
                args.append("-y")

        else:
            if self.VERSION and float(self.VERSION) >= 15.08:
                args.append("-aos")

        #: Exclude files
        for word in self.excludefiles:
            args.append("-xr!{}".format(word.strip()))

        #: Set a password
        password = kwargs.get("password")

        if password:
            args.append("-p{}".format(password))
        else:
            args.append("-p-")

        call = [self.CMD, command] + args + [arg for arg in xargs if arg]
        self.log_debug("EXECUTE " + " ".join(call))

        call = [to_str(cmd) for cmd in call]
        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

        renice(p.pid, self.priority)

        return p

    def _check_archive_encryption(self):
        if self.archive_encryption is None:
            p = self.call_cmd("l", "-slt", self.filename)
            out, err = (r.strip() if r else "" for r in p.communicate())

            encrypted_header = self._RE_ENCRYPTED_HEADER.search(err) is not None
            encrypted_files =  self._RE_ENCRYPTED_FILES.search(out) is not None

            self.archive_encryption = (encrypted_header, encrypted_files)

        return self.archive_encryption

    def _get_archive_info(self, password=None):
        if not self.archive_info:
            p = self.call_cmd("l", "-slt", self.filename, password=password)
            out, err = (r.strip() if r else "" for r in p.communicate())

            if err:
                if self._RE_ENCRYPTED_HEADER.search(err):
                    raise PasswordError

                elif any(e in err for e in ("Can not open", "cannot find the file")):
                    raise ArchiveError(self._("Cannot open file"))

                else:
                    raise ArchiveError(err)

            if p.returncode > 1:
                raise ArchiveError(self._("Process return code: {}").format(p.returncode))

            # Parse detailed list format (-slt)
            # The format is:
            # Path = filename
            # Size = 1024
            # Attributes = ...
            # <blank line>

            entries = []

            # Split the text into potential entry blocks (each starting with "Path =")
            blocks = re.split(r'\n(?=Path = )', out.strip())

            for file_block in blocks[2:]:  # Skip header block
                lines = file_block.strip().split('\n')
                file_entry = {}

                for line in lines:
                    if '=' in line:
                        key, value = [x.strip() for x in line.split('=', 1)]
                        file_entry[key] = value

                if 'Path' not in file_entry:
                    continue

                file_path = file_entry['Path']
                size_str = file_entry.get('Size', '0')
                attributes = file_entry.get('Attributes', "")

                try:
                    file_size = int(size_str)
                except ValueError:
                    file_size = 0

                # Build full destination path
                f = file_path
                if not self.fullpath:
                    f = os.path.basename(f)
                full_path = safejoin(self.dest, f, traversal=False)  # We check for path traversal on extraction

                entries.append({
                    'path': file_path,
                    'full_path': full_path,
                    'size': file_size,
                    'attributes': attributes,
                })

            self.archive_info = entries

        return self.archive_info

    def _find_smallest_file(self, password=None):
        if not self.smallest:
            smallest = (None, 0)

            archive_info = self._get_archive_info(password)
            for entry in archive_info:
                if smallest[1] == 0 or (smallest[1] > entry["size"] > 0):
                    smallest = (entry["path"], entry["size"])

            self.smallest = smallest

        return self.smallest

    def _detect_7zip_symlinks(self, password=None):
        """
        Detect symlinks in 7-Zip archive by parsing detailed list output.
        Raises ArchiveError if symlinks are found to prevent extraction.

        :param password: Archive password if needed
        :raises ArchiveError: If symlinks are detected in the archive
        """
        symlinks = []

        try:
            archive_info = self._get_archive_info(password)

            for entry in archive_info:
                current_file = entry["path"]
                attrs = entry["attributes"]  # Attributes = <perms with 'l' for symlinks>
                if 'l' in attrs:
                    symlinks.append(current_file)
                    self.log_warning(f"Found symlink in archive: {current_file}")

            if symlinks:
                raise ArchiveError(
                    f"Archive contains {len(symlinks)} symlink(s) - extraction blocked for security: {', '.join(symlinks[:5])}"
                )

        except ArchiveError:
            raise
        except Exception as e:
            self.log_warning(f"Error detecting symlinks in 7-Zip archive: {e}")
            # Don't fail hard on detection errors, post-extraction check will catch issues
