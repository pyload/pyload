# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import os
from builtins import int, object, range

from future import standard_library
from pyload.utils.fs import fullpath, lopen, remove

standard_library.install_aliases()


class ChunkInfo(object):

    def __init__(self, filename):
        self.path = fullpath(filename)
        self.size = 0
        self.resume = False
        self.chunks = []

    def __repr__(self):
        ret = "ChunkInfo: {0}, {1}{2}".format(self.path, self.size, os.linesep)
        for i, c in enumerate(self.chunks):
            ret += "{0}# {1}{2}".format(i, c[1], os.linesep)
        return ret

    def set_size(self, size):
        self.size = int(size)

    def add_chunk(self, name, range):
        self.chunks.append((name, range))

    def clear(self):
        self.chunks = []

    def create_chunks(self, chunks):
        self.clear()
        chunk_size = self.size // chunks

        current = 0
        for i in range(chunks):
            end = self.size - 1 if (i == chunks - 1) else current + chunk_size
            self.add_chunk("{0}.chunk{1}".format(self.path, i), (current, end))
            current += chunk_size + 1

    def save(self):
        filename = "{0}.chunks".format(self.path)
        with lopen(filename, mode='w') as fp:
            fp.write("name:{0}{1}".format(self.path, os.linesep))
            fp.write("size:{0}{1}".format(self.size, os.linesep))
            for i, c in enumerate(self.chunks):
                fp.write("#{0:d}:{1}".format(i, os.linesep))
                fp.write("\tname:{0}{1}".format(c[0], os.linesep))
                fp.write("\trange:{0:d}-{1:d}{2}".format(c[1][0], c[1][1], os.linesep))

    @staticmethod
    def load(name):
        filename = "{0}.chunks".format(name)
        if not os.path.isfile(filename):
            raise IOError
        with lopen(filename) as fp:
            name = fp.readline()[:-1]
            size = fp.readline()[:-1]
            if name.startswith("name:") and size.startswith("size:"):
                name = name[5:]
                size = size[5:]
            else:
                raise TypeError("chunk.file has wrong format")
            ci = ChunkInfo(name)
            ci.loaded = True
            ci.set_size(size)
            while True:
                if not fp.readline():  #: skip line
                    break
                name = fp.readline()[1:-1]
                range = fp.readline()[1:-1]
                if name.startswith("name:") and range.startswith("range:"):
                    name = name[5:]
                    range = range[6:].split("-")
                else:
                    raise TypeError("chunk.file has wrong format")

                ci.add_chunk(name, (int(range[0]), int(range[1])))
        return ci

    def remove(self):
        filename = "{0}.chunks".format(self.path)
        remove(filename)

    def get_count(self):
        return len(self.chunks)

    def get_chunk_name(self, index):
        return self.chunks[index][0]

    def get_chunk_range(self, index):
        return self.chunks[index][1]
