#!/usr/bin/env python
# -*- coding: utf-8 -*-



import sys
import tarfile

from .Extractor import ArchiveError, CRCError, Extractor
from .misc import encode


class UnTar(Extractor):
    __name__ = "UnTar"
    __type__ = "extractor"
    __version__ = "0.04"
    __status__ = "stable"

    __description__ = """TAR extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    VERSION = "{}.{}.{}".format(sys.version_info[0],
                            sys.version_info[1],
                            sys.version_info[2])

    @classmethod
    def isarchive(cls, filename):
        try:
            return tarfile.is_tarfile(encode(filename))
        except Exception:
            return False

    @classmethod
    def find(cls):
        return sys.version_info[:2] >= (2, 5)

    def list(self, password=None):
        with tarfile.open(self.filename) as t:
            self.files = t.getnames()
        return self.files

    def verify(self, password=None):
        try:
            t = tarfile.open(self.filename, errorlevel=1)

        except tarfile.CompressionError as e:
            raise CRCError(e)

        except (OSError, tarfile.TarError) as e:
            raise ArchiveError(e)

        else:
            t.close()

    def extract(self, password=None):
        self.verify(password)

        try:
            with tarfile.open(self.filename, errorlevel=2) as t:
                t.extractall(self.dest)
                self.files = t.getnames()
            return self.files

        except tarfile.ExtractError as e:
            self.log_warning(e)

        except tarfile.CompressionError as e:
            raise CRCError(e)

        except (OSError, tarfile.TarError) as e:
            raise ArchiveError(e)
