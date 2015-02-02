# -*- coding: utf-8 -*-

import os

from module.PyFile import PyFile


class ArchiveError(Exception):
    pass


class CRCError(Exception):
    pass


class PasswordError(Exception):
    pass


class Extractor:
    __name__    = "Extractor"
    __version__ = "0.18"

    __description__ = """Base extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "ranan@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    EXTENSIONS = []


    @classmethod
    def isArchive(cls, filename):
        name = os.path.basename(filename).lower()
        return any(name.endswith(ext) for ext in cls.EXTENSIONS)


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
        return [(fname, id) for fname, id in files_ids if cls.isArchive(fname)]


    def __init__(self, manager, filename, out,
                 fullpath=True,
                 overwrite=False,
                 excludefiles=[],
                 renice=0,
                 delete=False,
                 keepbroken=False,
                 fid=None):
        """ Initialize extractor for specific file """
        self.manager        = manager
        self.filename       = filename
        self.out            = out
        self.fullpath       = fullpath
        self.overwrite      = overwrite
        self.excludefiles   = excludefiles
        self.renice         = renice
        self.delete         = delete
        self.keepbroken     = keepbroken
        self.files          = []  #: Store extracted files here

        pyfile = self.manager.core.files.getFile(fid) if fid else None
        self.notifyProgress = lambda x: pyfile.setProgress(x) if pyfile else lambda x: None


    def init(self):
        """ Initialize additional data structures """
        pass


    def check(self):
        """Check if password if needed. Raise ArchiveError if integrity is
        questionable.

        :return: boolean
        :raises ArchiveError
        """
        raise PasswordError


    def isPassword(self, password):
        """ Check if the given password is/might be correct.
        If it can not be decided at this point return true.

        :param password:
        :return: boolean
        """
        return None


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
