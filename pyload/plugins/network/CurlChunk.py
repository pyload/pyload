# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################


from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
from builtins import range
from builtins import object
from past.utils import old_div
import re
from os import remove, stat, fsync
from os.path import exists
from time import sleep

import codecs
import pycurl

from pyload.network.HeaderDict import HeaderDict
from pyload.utils.fs import fs_encode, fs_decode, safe_filename

from .CurlRequest import CurlRequest


class ChunkInfo(object):
    def __init__(self, name):
        self.name = fs_decode(name)
        self.size = 0
        self.resume = False
        self.chunks = []

    def __repr__(self):
        ret = "ChunkInfo: %s, %s\n" % (self.name, self.size)
        for i, c in enumerate(self.chunks):
            ret += "%s# %s\n" % (i, c[1])

        return ret

    def setSize(self, size):
        self.size = int(size)

    def addChunk(self, name, range):
        self.chunks.append((name, range))

    def clear(self):
        self.chunks = []

    def createChunks(self, chunks):
        self.clear()
        chunk_size = old_div(self.size, chunks)

        current = 0
        for i in range(chunks):
            end = self.size - 1 if (i == chunks - 1) else current + chunk_size
            self.addChunk("%s.chunk%s" % (self.name, i), (current, end))
            current += chunk_size + 1


    def save(self):
        fs_name = fs_encode("%s.chunks" % self.name)
        fh = codecs.open(fs_name, "w", "utf_8")
        fh.write("name:%s\n" % self.name)
        fh.write("size:%s\n" % self.size)
        for i, c in enumerate(self.chunks):
            fh.write("#%d:\n" % i)
            fh.write("\tname:%s\n" % c[0])
            fh.write("\trange:%i-%i\n" % c[1])
        fh.close()

    @staticmethod
    def load(name):
        fs_name = fs_encode("%s.chunks" % name)
        if not exists(fs_name):
            raise IOError
        fh = codecs.open(fs_name, "r", "utf_8")
        name = fh.readline()[:-1]
        size = fh.readline()[:-1]
        if name.startswith("name:") and size.startswith("size:"):
            name = name[5:]
            size = size[5:]
        else:
            fh.close()
            raise TypeError("chunk.file has wrong format")
        ci = ChunkInfo(name)
        ci.loaded = True
        ci.setSize(size)
        while True:
            if not fh.readline(): #skip line
                break
            name = fh.readline()[1:-1]
            range = fh.readline()[1:-1]
            if name.startswith("name:") and range.startswith("range:"):
                name = name[5:]
                range = range[6:].split("-")
            else:
                raise TypeError("chunk.file has wrong format")

            ci.addChunk(name, (int(range[0]), int(range[1])))
        fh.close()
        return ci

    def remove(self):
        fs_name = fs_encode("%s.chunks" % self.name)
        if exists(fs_name): remove(fs_name)

    def getCount(self):
        return len(self.chunks)

    def getChunkName(self, index):
        return self.chunks[index][0]

    def getChunkRange(self, index):
        return self.chunks[index][1]

re_filename = re.compile(r"filename(?P<type>=|\*=(?P<enc>.+)'')(?P<name>.*)", re.I)


class CurlChunk(CurlRequest):
    def __init__(self, id, parent, range=None, resume=False):
        self.setContext(*parent.getContext())

        self.id = id
        self.p = parent # CurlDownload instance
        self.range = range # tuple (start, end)
        self.resume = resume
        self.log = parent.log

        self.size = range[1] - range[0] if range else -1
        self.arrived = 0
        self.lastURL = self.p.referer

        self.c = pycurl.Curl()

        self.header = ""
        self.headerParsed = False #indicates if the header has been processed
        self.headers = HeaderDict()

        self.fp = None #file handle

        self.initContext()

        self.BOMChecked = False # check and remove byte order mark

        self.rep = None

        self.sleep = 0.000
        self.lastSize = 0
        # next to last size
        self.nLastSize = 0

    def __repr__(self):
        return "<CurlChunk id=%d, size=%d, arrived=%d>" % (self.id, self.size, self.arrived)

    @property
    def cj(self):
        return self.p.context

    def getHandle(self):
        """ returns a Curl handle ready to use for perform/multiperform """

        self.setRequestContext(self.p.url, self.p.get, self.p.post, self.p.referer, self.p.cookies)
        self.c.setopt(pycurl.WRITEFUNCTION, self.writeBody)
        self.c.setopt(pycurl.HEADERFUNCTION, self.writeHeader)

        # request all bytes, since some servers in russia seems to have a defect arihmetic unit

        fs_name = fs_encode(self.p.info.getChunkName(self.id))
        if self.resume:
            self.fp = open(fs_name, "ab")
            self.arrived = self.fp.tell()
            if not self.arrived:
                self.arrived = stat(fs_name).st_size

            if self.range:
                #do nothing if chunk already finished
                if self.arrived + self.range[0] >= self.range[1]: return None

                if self.id == len(self.p.info.chunks) - 1: #as last chunk dont set end range, so we get everything
                    range = "%i-" % (self.arrived + self.range[0])
                else:
                    range = "%i-%i" % (self.arrived + self.range[0], min(self.range[1] + 1, self.p.size - 1))

                self.log.debug("Chunked resume with range %s" % range)
                self.c.setopt(pycurl.RANGE, range)
            else:
                self.log.debug("Resume File from %i" % self.arrived)
                self.c.setopt(pycurl.RESUME_FROM, self.arrived)

        else:
            if self.range:
                if self.id == len(self.p.info.chunks) - 1: # see above
                    range = "%i-" % self.range[0]
                else:
                    range = "%i-%i" % (self.range[0], min(self.range[1] + 1, self.p.size - 1))

                self.log.debug("Chunked with range %s" % range)
                self.c.setopt(pycurl.RANGE, range)

            self.fp = open(fs_name, "wb")

        return self.c

    def writeHeader(self, buf):
        self.header += buf
        #@TODO forward headers?, this is possibly unneeded, when we just parse valid 200 headers
        # as first chunk, we will parse the headers
        if not self.range and self.header.endswith("\r\n\r\n"):
            self.parseHeader()
        elif not self.range and buf.startswith("150") and "data connection" in buf: #ftp file size parsing
            size = re.search(r"(\d+) bytes", buf)
            if size:
                self.p._size = int(size.group(1))
                self.p.chunkSupport = True

        self.headerParsed = True

    def writeBody(self, buf):
        #ignore BOM, it confuses unrar
        if not self.BOMChecked:
            if [ord(b) for b in buf[:3]] == [239, 187, 191]:
                buf = buf[3:]
            self.BOMChecked = True

        size = len(buf)
        self.nLastSize = self.lastSize
        self.lastSize = size

        self.arrived += size

        self.fp.write(buf)

        if self.p.bucket:
            sleep(self.p.bucket.consumed(size))

        # if the buffer sizes are stable no sleep will be made
        elif size != self.lastSize or size != self.nLastSize:
            # Avoid small buffers, increasing sleep time slowly if buffer size gets smaller
            # otherwise reduce sleep time percentile (values are based on tests)
            # So in general cpu time is saved without reducing bandwidth too much

            if size < self.lastSize:
                self.sleep += 0.002
            else:
                self.sleep *= 0.7

            sleep(self.sleep)

        if self.range and self.arrived > self.size:
            return 0 #close if we have enough data


    def parseHeader(self):
        """parse data from received header"""
        for orgline in self.decodeResponse(self.header).splitlines():
            line = orgline.strip().lower()
            if line.startswith("accept-ranges") and "bytes" in line:
                self.p.chunkSupport = True

            if "content-disposition" in line:

                m = re_filename.search(orgline.strip())
                if m:
                    name = safe_filename(m.groupdict()['name']).strip("\"' ")
                    self.p._name = name
                    self.log.debug("Content-Disposition: %s" % name)

            if not self.resume and line.startswith("content-length"):
                self.p._size = int(line.split(":")[1])

        self.headerParsed = True

    def stop(self):
        """The download will not proceed after next call of writeBody"""
        self.range = [0, 0]
        self.size = 0

    def resetRange(self):
        """ Reset the range, so the download will load all data available  """
        self.range = None

    def setRange(self, range):
        self.range = range
        self.size = range[1] - range[0]

    def flushFile(self):
        """  flush and close file """
        self.fp.flush()
        fsync(self.fp.fileno()) #make sure everything was written to disk
        self.fp.close() #needs to be closed, or merging chunks will fail

    def close(self):
        """ closes everything, unusable after this """
        if self.fp: self.fp.close()
        self.c.close()
        if hasattr(self, "p"): del self.p
