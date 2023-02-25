# -*- coding: utf-8 -*-

import os
import re

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
        excludefiles=[],
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
        self.excludefiles = excludefiles
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
