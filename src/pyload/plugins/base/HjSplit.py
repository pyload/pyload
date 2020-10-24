# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import re

from .Extractor import ArchiveError, BaseExtractor
from ..helpers import exists


class HjSplit(BaseExtractor):
    __name__ = "HjSplit"
    __type__ = "extractor"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = """HJSPLIT extractor plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    VERSION = __version__

    EXTENSIONS = [("001", r'(?<!7z\.)001')]

    _RE_PART = re.compile(r"(?<!\.7z)\.\d{3}$")

    BUFFER_SIZE = 4096

    @classmethod
    def find(cls):
        return True

    @classmethod
    def ismultipart(cls, filename):
        return True if cls._RE_PART.search(filename) else False

    def chunks(self):
        files = []
        dir, name = os.path.split(self.filename)

        #: eventually Multipart Files
        files.extend(os.path.join(dir, os.path.basename(f))
                     for f in filter(self.ismultipart, [x[1]["name"] for x in self.pyfile.package().getChildren().items()])
                     if self._RE_PART.sub("", name) == self._RE_PART.sub("", f))

        #: Actually extracted file
        if self.filename not in files:
            files.append(self.filename)

        return files

    def list(self, password=None):
        return [self.filename[:-4]]

    def extract(self, password=None):
        file_list = []
        size_total = 0
        name = os.path.basename(self.filename)[:-4]

        chunks = sorted(self.chunks())
        num_chunks = len(chunks)

        #: Verify HjSplit consistency
        if len(chunks) == 1:
            raise ArchiveError("Cannot merge just one chunk '{}'".format(chunks[0]))

        for i in range(0, num_chunks):
            if not exists(chunks[i]):
                raise ArchiveError("Chunk '{}' not found".format(chunks[i]))

            if i == 0:
                chunk_size = os.path.getsize(chunks[i])

            else:
                if int(chunks[i][-3:]) != i + 1:
                    missing_chunk = "{}.{:0>3d}".format(os.path.splitext(chunks[i])[0], i + 1)
                    raise ArchiveError("Chunk '{}' is missing".format(missing_chunk))

                if i < num_chunks - 1:
                    if os.path.getsize(chunks[i]) != chunk_size:
                        raise ArchiveError("Invalid chunk size for chunk '{}'".format(chunks[i]))

                    size_total += chunk_size

                else:
                    size_total += os.path.getsize(chunks[i])

        #: Now do the actual merge
        with open(os.path.join(self.dest, name), "wb") as output_file:
            size_written = 0
            for part_filename in chunks:
                self.log_debug("Merging part", part_filename)

                with open(part_filename, "rb") as part_file:
                    while True:
                        f_buffer = part_file.read(self.BUFFER_SIZE)
                        if f_buffer:
                            output_file.write(f_buffer)
                            size_written += len(f_buffer)
                            self.pyfile.set_progress((size_written * 100) / size_total)
                        else:
                            break

                self.log_debug("Finished merging part", part_filename)

            self.pyfile.setProgress(100)
