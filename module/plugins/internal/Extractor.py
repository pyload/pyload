# -*- coding: utf-8 -*-

import os
import re

from module.PyFile import PyFile
from module.plugins.internal.Plugin import Plugin
from module.plugins.internal.utils import encode


class ArchiveError(Exception):
    pass


class CRCError(Exception):
    pass


class PasswordError(Exception):
    pass


class Extractor(Plugin):
    __name__    = "Extractor"
    __type__    = "extractor"
    __version__ = "0.40"
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
        return any(name.endswith(ext) for ext in cls.EXTENSIONS)


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

        for fname, id, fout in files_ids:
            if cls.isarchive(fname):
                pname = re.sub(cls.re_multipart, "", fname) if cls.ismultipart(fname) else os.path.splitext(fname)[0]
                if pname not in processed:
                    processed.append(pname)
                    targets.append((fname, id, fout))

        return targets


    def __init__(self, plugin, filename, out,
                 fullpath=True,
                 overwrite=False,
                 excludefiles=[],
                 renice=False,
                 priority=0,
                 keepbroken=False,
                 fid=None):
        """
        Initialize extractor for specific file
        """
        self._init(plugin.pyload)

        self.plugin       = plugin
        self.filename     = filename
        self.out          = out
        self.fullpath     = fullpath
        self.overwrite    = overwrite
        self.excludefiles = excludefiles
        self.priority     = priority
        self.keepbroken   = keepbroken
        self.files        = []  #: Store extracted files here

        pyfile = self.pyload.files.getFile(fid) if fid else None
        self.notify_progress = lambda x: pyfile.setProgress(x) if pyfile else lambda x: None

        self.init()


    @property
    def target(self):
        return encode(self.filename)


    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.__name__,) + messages
        return self.plugin._log(level, plugintype, self.plugin.__name__, messages)


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


    def items(self):
        """
        Return list of archive parts
        """
        return [self.filename]


    def list(self, password=None):
        """
        Populate self.files at some point while extracting
        """
        return self.files
