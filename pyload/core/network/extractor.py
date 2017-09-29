# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library

standard_library.install_aliases()


class ArchiveError(Exception):

    __slots__ = []


class CRCError(Exception):

    __slots__ = []


class WrongPassword(Exception):

    __slots__ = []


class AbtractExtractor(object):

    __version__ = "0.1"

    @staticmethod
    def check_deps():
        """
        Check if system satisfies dependencies
        :return: boolean
        """
        return True

    @staticmethod
    def get_targets(files_ids):
        """
        Filter suited targets from list of filename id tuple list
        :param files_ids: List of file paths
        :return: List of targets, id tuple list
        """
        raise NotImplementedError

    def __init__(self, m, filename, out, fullpath,
                 overwrite, excludefiles, renice):
        """
        Initialize extractor for specific file

        :param m: ExtractArchive addon plugin
        :param path: Absolute file path
        :param out: Absolute path to destination directory
        :param fullpath: Extract to fullpath
        :param overwrite: Overwrite existing archives
        :param renice: Renice value
        """
        self.__manager = m
        self.filename = filename
        self.out = out
        self.fullpath = fullpath
        self.overwrite = overwrite
        self.excludefiles = excludefiles
        self.renice = renice
        self.files = []  # Store extracted files here

    def init(self):
        """
        Initialize additional data structures.
        """
        pass

    def check_archive(self):
        """
        Check if password is needed. Raise ArchiveError if integrity is
        questionable.

        :return: boolean
        :raises ArchiveError
        """
        return False

    def check_password(self, password):
        """
        Check if the given password is/might be correct.
        If it can not be decided at this point return true.

        :param password:
        :return: boolean
        """
        return True

    def extract(self, progress, password=None):
        """
        Extract the archive. Raise specific errors in case of failure.

        :param progress: Progress function, call this to update status
        :param password password to use
        :raises WrongPassword
        :raises CRCError
        :raises ArchiveError
        :return:
        """
        raise NotImplementedError

    def get_delete_files(self):
        """
        Return list of files to delete, do *not* delete them here.

        :return: List with paths of files to delete
        """
        raise NotImplementedError

    def get_extracted_files(self):
        """
        Populate self.files at some point while extracting.
        """
        return self.files
