# -*- coding: utf-8 -*-

import os
import re

from module.PyFile import PyFile


class ArchiveError(Exception):
    pass


class CRCError(Exception):
    pass


class PasswordError(Exception):
    pass


class Extractor:
    __name__    = "Extractor"
    __version__ = "0.24"

    __description__ = """Base extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("Immenz"        , "immenz@gmx.net"   )]


    EXTENSIONS = []
    VERSION    = ""
    REPAIR     = False


    @classmethod
    def isArchive(cls, filename):
        name = os.path.basename(filename).lower()
        return any(name.endswith(ext) for ext in cls.EXTENSIONS)


    @classmethod
    def isMultipart(cls, filename):
        return False


    @classmethod
    def isUsable(cls):
        """ Check if system statisfy dependencies
        :return: boolean
        """
        return None


    @classmethod
    def getTargets(cls, files_ids):
        """ Filter suited targets from list of filename id tuple list
        :param files_ids: List of filepathes
        :return: List of targets, id tuple list
        """
        targets = []
        processed = []

        for fname, id, fout in files_ids:
            if cls.isArchive(fname):
                pname = re.sub(cls.re_multipart, '', fname) if cls.isMultipart(fname) else os.path.splitext(fname)[0]
                if pname not in processed:
                    processed.append(pname)
                    targets.append((fname, id, fout))
        return targets


    def __init__(self, manager, filename, out,
                 fullpath=True,
                 overwrite=False,
                 excludefiles=[],
                 renice=0,
                 delete='No',
                 keepbroken=False,
                 fid=None):
        """ Initialize extractor for specific file """
        self.manager      = manager
        self.filename     = filename
        self.out          = out
        self.fullpath     = fullpath
        self.overwrite    = overwrite
        self.excludefiles = excludefiles
        self.renice       = renice
        self.delete       = delete
        self.keepbroken   = keepbroken
        self.files        = []  #: Store extracted files here

        pyfile = self.manager.core.files.getFile(fid) if fid else None
        self.notifyProgress = lambda x: pyfile.setProgress(x) if pyfile else lambda x: None


    def init(self):
        """ Initialize additional data structures """
        pass


    def check(self):
        """Quick Check by listing content of archive.
        Raises error if password is needed, integrity is questionable or else.

        :raises PasswordError
        :raises CRCError
        :raises ArchiveError
        """
        raise NotImplementedError

    def verify(self):
        """Testing with Extractors buildt-in method
        Raises error if password is needed, integrity is questionable or else.

        :raises PasswordError
        :raises CRCError
        :raises ArchiveError
        """
        raise NotImplementedError


    def repair(self):
        return None


    def extract(self, password=None):
        """Extract the archive. Raise specific errors in case of failure.

        :param progress: Progress function, call this to update status
        :param password password to use
        :raises PasswordError
        :raises CRCError
        :raises ArchiveError
        :return:
        """
        raise NotImplementedError


    def getDeleteFiles(self):
        """Return list of files to delete, do *not* delete them here.

        :return: List with paths of files to delete
        """
        return [self.filename]


    def list(self, password=None):
        """Populate self.files at some point while extracting"""
        return self.files
