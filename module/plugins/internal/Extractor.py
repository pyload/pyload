# -*- coding: utf-8 -*-

import os
import re

from module.PyFile import PyFile
from module.plugins.internal.Plugin import Plugin
from module.plugins.internal.misc import encode


class ArchiveError(Exception):
    pass


class CRCError(Exception):
    pass


class PasswordError(Exception):
    pass


class Extractor(Plugin):
    __name__    = "Extractor"
    __type__    = "extractor"
    __version__ = "0.42"
    __status__  = "stable"

    __description__ = """Base extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("Immenz"        , "immenz@gmx.net"   )]


    EXTENSIONS = []
    REPAIR     = False
    VERSION    = None


    @classmethod
    def isarchive(cls, filename):
        name = os.path.basename(filename).lower()
        return any(name.endswith('.' + ext) for ext in cls.EXTENSIONS)


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
        targets   = []
        processed = []

        for id, fname, fout in files_ids:
            if not cls.isarchive(fname):
                continue

            if cls.ismultipart(fname):
                pname = re.sub(cls._RE_PART, "", fname)
            else:
                pname = os.path.splitext(fname)[0]

            if pname in processed:
                continue

            processed.append(pname)
            targets.append((id, fname, fout))

        return targets


    def __init__(self, pyfile, filename, out,
                 fullpath=True,
                 overwrite=False,
                 excludefiles=[],
                 priority=0,
                 keepbroken=False):
        """
        Initialize extractor for specific file
        """
        self._init(pyfile.m.core)

        self.pyfile       = pyfile
        self.filename     = filename
        self.name         = os.path.basename(filename)
        self.out          = out
        self.fullpath     = fullpath
        self.overwrite    = overwrite
        self.excludefiles = excludefiles
        self.priority     = priority
        self.keepbroken   = keepbroken
        self.progress     = lambda x: pyfile.setProgress(int(x))

        self.init()


    @property
    def target(self):
        return encode(self.filename)


    @property
    def dest(self):
        return encode(self.out)


    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.__name__,) + messages
        return self.pyfile.plugin._log(level, plugintype, self.pyfile.plugin.__name__, messages)


    def verify(self, password=None):
        """
        Testing with Extractors built-in method
        Raise error if password is needed, integrity is questionable or else
        """
        pass


    def repair(self):
        pass


    def extract(self, password=None):
        """
        Extract the archive
        Raise specific errors in case of failure
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
