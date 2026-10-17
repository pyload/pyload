import os
import re
import subprocess

# test: python -m src.pyload.plugins.extractors.UnRar

if __name__ == "__main__":
    import sys
    # fix: ModuleNotFoundError: No module named 'pyload'
    sys.path.insert(0, os.path.normpath(os.path.dirname(__file__) + "/../../.."))

from pyload import PKGDIR
from pyload.core.utils.convert import to_str
from pyload.core.utils.fs import safejoin
from pyload.plugins.base.extractor import ArchiveError, BaseExtractor, CRCError, PasswordError
from pyload.plugins.helpers import renice


class UnRar(BaseExtractor):
    __name__ = "UnRar"
    __type__ = "extractor"
    __version__ = "1.49"
    __status__ = "testing"

    __config__ = [
        ("ignore_warnings", "bool", "Ignore unrar warnings", False),
        ("ignore_file_attributes", "bool", "Ignore File Attributes", False)
    ]

    __description__ = """RAR extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Immenz", "immenz@gmx.net"),
        ("GammaCode", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    CMD = "unrar"
    EXTENSIONS = [
        "rar",
        "cab",
        "arj",
        "lzh",
        "tar",
        "gz",
        "ace",
        "uue",
        "bz2",
        "jar",
        "iso",
        "xz",
        "z",
    ]

    _RE_PART = re.compile(r"\.(part|r)\d+(\.rar|\.rev)?(\.bad)?|\.rar$", re.I)
    _RE_FIXNAME = re.compile(r"Building (.+)")
    _RE_FILES_V4 = re.compile(
        r"^([* ])(.+?)\s+(\d+)\s+(\d+)\s+(\d+%|-->|<--)\s+([\d-]+)\s+([\d:]+)\s*([ACHIRS.rw\-]+)\s+([0-9A-F]{8})\s+(\w+)\s+([\d.]+)",
        re.M
    )
    _RE_FILES_V5 = re.compile(
        r"^([* ])\s*([ACHIRS.rw\-]+)\s+(\d+)(?:\s+\d+)?(?:\s+(?:\d+%|-->|<--))?\s+([\d-]+)\s+([\d:]+)(?:\s+[0-9A-F]{8})?\s+(.+)",
        re.M
    )
    _RE_ENCRYPTED_HEADER = re.compile(r'\s0 files')
    _RE_BADPWD = re.compile(r"password", re.I)
    _RE_BADCRC = re.compile(
        r"encrypted|damaged|CRC failed|checksum error|corrupt", re.I
    )
    _RE_VERSION = re.compile(r"(?:UN)?RAR\s(\d+\.\d+)", re.I)

    @classmethod
    def find(cls):
        try:
            if os.name == "nt":
                cls.CMD = safejoin(PKGDIR, "lib", "RAR.exe")
            else:
                cls.CMD = "rar"

            p = subprocess.Popen(
                [cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = (to_str(r).strip() if r else "" for r in p.communicate())
            cls.REPAIR = True

        except OSError:
            try:
                if os.name == "nt":
                    cls.CMD = safejoin(PKGDIR, "lib", "UnRAR.exe")
                else:
                    cls.CMD = "unrar"

                p = subprocess.Popen(
                    [cls.CMD], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                out, err = (to_str(r).strip() if r else "" for r in p.communicate())

            except OSError:
                return False

        m = cls._RE_VERSION.search(out)
        if m is not None:
            cls.VERSION = m.group(1)
            cls._RE_FILES = cls._RE_FILES_V4 if float(cls.VERSION) < 5 else cls._RE_FILES_V5
            return True

        else:
            return False

    @classmethod
    def ismultipart(cls, filename):
        return cls._RE_PART.search(filename) is not None

    def init(self):
        self.smallest = None
        self.files_raw = None
        self.archive_encryption = None

    def verify(self, password=None):
        #: First we check if the header (file list) is protected
        #: if the header is protected, we cen verify the password very fast without hassle.
        #: otherwise we find the smallest file in the archive and then try to extract it
        encrypted_header, encrypted_files = self._check_archive_encryption()
        if encrypted_header:
            p = self.call_cmd("l", "-v", self.filename, password=password)
            out, err = (_r.strip() if _r else "" for _r in p.communicate())

            if self._RE_ENCRYPTED_HEADER.search(out):
                raise PasswordError

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

            except (PasswordError, CRCError, ArchiveError) as ex:
                try:
                    os.remove(extracted)
                except OSError:
                    pass

                raise ex

    def repair(self):
        p = self.call_cmd("rc", self.filename)

        #: Communicate and retrieve stderr
        self.progress(p)
        out, err = (to_str(r).strip() if r else "" for r in p.communicate())

        if err or p.returncode:
            p = self.call_cmd("r", self.filename)

            # communicate and retrieve stderr
            self.progress(p)
            out, err = (to_str(r).strip() if r else "" for r in p.communicate())

            if err or p.returncode:
                return False

            else:
                dir = os.path.dirname(self.filename)
                name = self._RE_FIXNAME.search(out).group(1)

                self.filename = safejoin(dir, name)

        return True

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
        file_list = self._list_raw(password)
        if file_list:
            self.log_debug(f"extract: file_list: {file_list}")
            self._validate_archive_entries(file_list)

        self.log_debug(f"extract: archive entries are valid")

        self.log_debug(f"extract: extracting to {self.dest}")

        # "rar x" does not create self.dest
        os.makedirs(self.dest, exist_ok=True)

        p = self.call_cmd(command, self.filename, file, self.dest, password=password)

        self.log_debug(f"extract: p={p}")

        #: Communicate and retrieve stderr
        self.progress(p)
        out, err = (to_str(r).strip() if r else "" for r in p.communicate())

        self.log_debug(f"extract: out={out}")
        self.log_debug(f"extract: err={err}")

        if err:
            if self._RE_BADPWD.search(err):
                raise PasswordError

            elif self._RE_BADCRC.search(err):
                raise CRCError(err)

            elif self.config.get("ignore_warnings", False) and err.startswith(
                "WARNING:"
            ):
                pass

            else:  #: Raise error if anything is on stderr
                raise ArchiveError(err)

        self.log_debug(f"extract: p.returncode={p.returncode}")

        if p.returncode and p.returncode != 10:  #: RARX_NOFILES:
            raise ArchiveError(self._("Process return code: {}").format(p.returncode))

        return self.files

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
            self.log_debug(f"UnRar.list: calling _find_smallest_file")
            self._find_smallest_file(password=password)

        return self.files

    def call_cmd(self, command, *xargs, **kwargs):
        args = []

        if float(self.VERSION) >= 5.5:
            #: Specify UTF-8 encoding
            args.append("-scf")

        #: Overwrite flag
        if self.overwrite:
            args.append("-o+")
        else:
            args.append("-o-")
            args.append("-or")

        for word in self.excludefiles:
            args.append("-x{}".format(word.strip()))

        #: Assume yes on all queries
        args.append("-y")

        #: Disable comments show
        args.append("-c-")

        #: Set a password
        password = kwargs.get("password")

        if password:
            args.append("-p{}".format(password))
        else:
            args.append("-p-")

        if self.keepbroken:
            args.append("-kb")

        if self.config.get("ignore_file_attributes", False):
            args.append("-ai")

        # Skip symbolic links to prevent symlink escape attacks
        args.append("-ol-")

        # NOTE: return codes are not reliable, some kind of threading, cleanup
        # whatever issue
        call = [self.CMD, command] + args + [arg for arg in xargs if arg]
        self.log_debug("EXECUTE " + " ".join(call))

        call = [to_str(cmd) for cmd in call]

        import shlex
        self.log_debug(f"call_cmd: call: {shlex.join(call)}")

        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

        renice(p.pid, self.priority)

        return p

    def _check_archive_encryption(self):
        if self.archive_encryption is None:
            p = self.call_cmd("l", "-v", self.filename)
            out, err = (_r.strip() if _r else "" for _r in p.communicate())
            encrypted_header = self._RE_ENCRYPTED_HEADER.search(out) is not None
            encrypted_files = any((m.group(1) == "*" for m in self._RE_FILES.finditer(out)))

            self.archive_encryption = (encrypted_header, encrypted_files)

        return self.archive_encryption

    def _list_raw(self, password=None):
        if not self.files_raw:
            self._find_smallest_file(password)

        return self.files_raw

    def _find_smallest_file(self, password=None):
        if not self.smallest:
            command = "v" if self.fullpath else "l"
            self.log_debug(f"UnRar._find_smallest_file: command={command}")
            p = self.call_cmd(command, "-v", self.filename, password=password)
            out, err = (_r.strip() if _r else "" for _r in p.communicate())

            if "Cannot open" in err:
                raise ArchiveError(_("Cannot open file"))

            if err:  #: Only log error at this point
                self.log_error(err)

            self.log_debug(f"UnRar._find_smallest_file: self.fullpath={self.fullpath}")

            self.log_debug(f"UnRar._find_smallest_file: self.dest={self.dest}")

            smallest = (None, 0)
            files = set()
            files_raw = set()
            f_grp = 5 if float(self.VERSION) >= 5 else 1
            # self.log_debug(f"UnRar._find_smallest_file: out={out}")
            for groups in self._RE_FILES.findall(out):
                self.log_debug(f"UnRar._find_smallest_file: groups={groups}")
                s = int(groups[2])
                f = groups[f_grp].strip()
                self.log_debug(f"UnRar._find_smallest_file: f={f}")

                files_raw.add(f)

                if smallest[1] == 0 or smallest[1] > s > 0:
                    smallest = (f, s)

                r'''
                if not self.fullpath:
                    f = os.path.basename(f)
                    self.log_debug(f"UnRar._find_smallest_file: basename -> f={f}")
                '''

                # 5f4f0fa5fe 2026-03-15 f = safejoin(self.dest, f)
                # 7680874837 2022-03-19 f = os.path.join(self.dest, f)
                # bec7ac7995 2022-03-19 f = os.path.join(self.dest, f)
                # edfc2907fa 2020-12-05 files.add(os.path.join(self.dest, f))
                #   stupid GammaC0de broke git history
                #   by moving and patching files in the same commit
                #   a: src/pyload/plugins/base/unrar.py
                #   b: src/pyload/plugins/extractors/UnRar.py
                # 9b18d0b09c 2018-12-17 result.add(os.path.join(self.dest, os.path.basename(filename)))
                # bec75defda 2018-10-16 result.add(os.path.join(self.dest, os.path.basename(f)))
                # 1244d3ecd5 2018-12-05 rename
                #   a: src/pyload/plugins/internal/unrar.py
                #   b: src/pyload/plugins/base/unrar.py
                # d8096353ba 2015-12-14 result.add(fsjoin(self.dest, os.path.basename(f)))
                # ...
                # -> always has been like this: self.files has absolute file paths
                # so BaseExtractor._validate_archive_entries is wrong since
                # ad249dd5b0 2026-05-26 if normalized.startswith("/"):
                # f09201955c 2026-05-23 if os.path.isabs(entry_path):
                r'''
                f = safejoin(self.dest, f)
                self.log_debug(f"UnRar._find_smallest_file: safejoin -> f={f}")
                '''

                self.make_it_break = True
                if getattr(self, "make_it_break", False):
                    self.log_debug(f"UnRar._find_smallest_file: make_it_break=True")
                    r'''
                    if not self.fullpath:
                        f = os.path.basename(f)
                        self.log_debug(f"UnRar._find_smallest_file: basename -> f={f}")
                    '''
                    f = safejoin(self.dest, f)
                    self.log_debug(f"UnRar._find_smallest_file: safejoin -> f={f}")
                else:
                    self.log_debug(f"UnRar._find_smallest_file: make_it_break=False")
                files.add(f)

            # test: ArchiveError: Attempted path traversal in archive
            # files.add("/bad/absolute/path")
            # files.add("../../../bad/relative/path")

            self.smallest = smallest
            self.files_raw = list(files_raw)
            self.files = list(files)

        return self.smallest


if __name__ == "__main__":

    # FIXME refactor with src/pyload/plugins/decrypters/SerienfansOrg.py
    # FIXME log_debug should work
    import logging
    from pyload.core.managers.file_manager import FileManager
    from pyload.core.network.request_factory import RequestFactory
    pyload_config = {
        "general": {
            "ssl_verify": False, # Verify SSL certificates
        },
        "download": {
            "ipv6": True, # allow ipv6
            "interface": "", # Download interface to bind (IP Address)
            "limit_speed": None,
        },
        "proxy": {
            "enabled": False,
        },
    }
    pyload_plugin_config = {
        "UnRar": {
            "ignore_warnings": False, # Ignore unrar warnings
            "ignore_file_attributes": False, # Ignore File Attributes
        },
    }
    class MockConfig:
        def get(self, scope, key):
            try:
                return pyload_config[scope][key]
            except KeyError:
                pass
            print("MockConfig.get", scope, key)
            return None
        def get_plugin(self, scope, key):
            try:
                return pyload_plugin_config[scope][key]
            except KeyError:
                pass
            print("MockConfig.get_plugin", scope, key)
            return None
    class MockPyload:
        log = logging.getLogger(__name__)
        #debug = 1 # compact debug log
        debug = 2 # trace debug log
        config = MockConfig()
        tempdir = "/tmp/pyLoad" # pyload.tempdir
        def __init__(self):
            self.log.setLevel(logging.DEBUG)
            self.files = self.file_manager = FileManager(self)
            self.req = self.request_factory = RequestFactory(self)
        def _(self, *a, **k):
            # translator function?
            return a[0]
    mock_pyload = MockPyload()
    class MockPackage:
        password = None
    class MockPyFile:
        url = "http://localhost:99999999/"
        id = 123
        # set status for check_status in pyload/plugins/base/hoster.py
        # pyload.core.datatypes.enums.DownloadStatus.STARTING = 7
        status = 7
        abort = False
        _ = mock_pyload._
        def __init__(
            # actually "manager" is pyload.files
            # self.files = self.file_manager = FileManager(self)
            # self, manager, id, url, name, size, status, error, pluginname, package, order
            self, *args, **kwargs
        ):
            if args:
                print("MockPyFile.__init__: args", args, kwargs)
                manager, id, url, name, size, status, error, pluginname, package, order = args
                self.id = id
                self.url = url
                self.name = name
                self.size = size
                self.status = status
            #self.m = self.manager = manager
            self.m = self.manager = mock_pyload.files
            self._package = MockPackage()
        def package(self):
            return self._package
        def set_progress(self, progress_percent):
            print(f"pyfile.set_progress: {progress_percent}%")


    import sys

    filename = sys.argv[1] # path/to/test.rar

    try:
        password = sys.argv[2]
    except IndexError:
        password = None

    out = filename + ".out"

    pyfile = MockPyFile()

    assert os.path.exists(filename)

    # set self.VERSION
    assert UnRar.find() == True

    # # force absolute path
    # filename = os.path.abspath(filename)

    unrar = UnRar(pyfile, filename, out)

    # not working
    r'''
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    for n in ("debug", "error", "warning", "info"):
        setattr(unrar, f"log_{n}", getattr(logger, n))
    '''

    for n in ("debug", "error", "warning", "info"):
        setattr(unrar, f"log_{n}", print)

    # # ensure unrar is using absolute path
    # assert unrar.fullpath == True

    unrar.make_it_break = True

    # FIXME ArchiveError: Attempted path traversal in archive
    # self._validate_archive_entries(file_list)
    files = unrar.extract(password=password)
    print("extracted files:", files)

r'''
echo hello >test.txt
rar a test.rar test.txt
# good: relative filepath
python -m src.pyload.plugins.extractors.UnRar test.rar
# bad: absolute filepath
# ArchiveError: Attempted path traversal in archive
python -m src.pyload.plugins.extractors.UnRar "$PWD"/test.rar
'''
