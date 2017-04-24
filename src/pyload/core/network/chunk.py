# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals
from future import standard_library

import io
import os
from builtins import int, object, range

from pyload.utils import format
from pyload.utils.path import remove

standard_library.install_aliases()


class ChunkInfo(object):

    def __init__(self, name):
        self.name = name
        self.size = 0
        self.resume = False
        self.chunks = []

    def __repr__(self):
        ret = "ChunkInfo: {0}, {1}\n".format(self.name, self.size)
        for i, c in enumerate(self.chunks):
            ret += "{0}# {1}\n".format(i, c[1])

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
            self.add_chunk("{0}.chunk{1}".format(self.name, i), (current, end))
            current += chunk_size + 1

    def save(self):
        fs_name = format.path("{0}.chunks".format(self.name))
        with io.open(fs_name, mode='w') as fp:
            fp.write("name:{0}\n".format(self.name))
            fp.write("size:{0}\n".format(self.size))
            for i, c in enumerate(self.chunks):
                fp.write("#{0:d}:\n".format(i))
                fp.write("\tname:{0}\n".format(c[0]))
                fp.write("\trange:{0:d}-{1:d}\n".format(*c[1]))

    @staticmethod
    def load(name):
        fs_name = format.path("{0}.chunks".format(name))
        if not os.path.exists(fs_name):
            raise IOError
        with io.open(fs_name) as fp:
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
        fs_name = format.path("{0}.chunks".format(self.name))
        remove(fs_name)

    def get_count(self):
        return len(self.chunks)

    def get_chunk_name(self, index):
        return self.chunks[index][0]

    def get_chunk_range(self, index):
        return self.chunks[index][1]
