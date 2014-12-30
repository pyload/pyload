# -*- coding: utf-8 -*-

class ArchiveError(Exception):
    pass


class CRCError(Exception):
    pass


class PasswordError(Exception):
    pass


class Extractor:
    __name__    = "Extractor"
    __version__ = "0.13"

    __description__ = """Base extractor plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "ranan@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    EXTENSIONS = []


    @classmethod
    def checkDeps(cls):
        """ Check if system statisfy dependencies
        :return: boolean
        """
        return True


    @classmethod
    def isArchive(cls, file):
        raise NotImplementedError


    @classmethod
    def getTargets(cls, files_ids):
        """ Filter suited targets from list of filename id tuple list
        :param files_ids: List of filepathes
        :return: List of targets, id tuple list
        """
        targets = []

        for file, id in files_ids:
            if cls.isArchive(file):
                targets.append((file, id))

        return targets


    def __init__(self, m, file, out, password, fullpath, overwrite, excludefiles, renice, delete, keepbroken):
        """Initialize extractor for specific file

        :param m: ExtractArchive Hook plugin
        :param file: Absolute filepath
        :param out: Absolute path to destination directory
        :param fullpath: extract to fullpath
        :param overwrite: Overwrite existing archives
        :param renice: Renice value
        """
        self.m            = m
        self.file         = file
        self.out          = out
        self.password     = password
        self.fullpath     = fullpath
        self.overwrite    = overwrite
        self.excludefiles = excludefiles
        self.renice       = renice
        self.delete       = delete
        self.keepbroken   = keepbroken
        self.files        = []  #: Store extracted files here


    def init(self):
        """ Initialize additional data structures """
        pass


    def verify(self):
        """Check if password if needed. Raise ArchiveError if integrity is
        questionable.

        :raises ArchiveError
        """
        pass


    def isPassword(self, password):
        """ Check if the given password is/might be correct.
        If it can not be decided at this point return true.

        :param password:
        :return: boolean
        """
        if isinstance(password, basestring):
            return True
        else:
            return False


    def setPassword(self, password):
        if self.isPassword(password):
            self.password = password
            return True
        else:
            return False


    def repair(self):
        return False


    def extract(self, progress=lambda x: None):
        """Extract the archive. Raise specific errors in case of failure.

        :param progress: Progress function, call this to update status
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
        raise NotImplementedError


    def getExtractedFiles(self):
        """Populate self.files at some point while extracting"""
        return self.files
