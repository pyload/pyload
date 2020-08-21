#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
"""
import codecs
import os
import re
import time
import urllib
from cgi import parse_header
from email.header import decode_header
from ntpath import basename as ntpath_basename
from posixpath import basename as posixpath_basename

import pycurl
from HTTPRequest import HTTPRequest
from module.utils import decode, fs_encode


class WrongFormat(Exception):
    pass


class ChunkInfo():
    def __init__(self, name):
        self.name = decode(name)
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
        chunk_size = self.size / chunks

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
        if not os.path.exists(fs_name):
            raise IOError()
        fh = codecs.open(fs_name, "r", "utf_8")
        name = fh.readline()[:-1]
        size = fh.readline()[:-1]
        if name.startswith("name:") and size.startswith("size:"):
            name = name[5:]
            size = size[5:]
        else:
            fh.close()
            raise WrongFormat()
        ci = ChunkInfo(name)
        ci.loaded = True
        ci.setSize(size)
        while True:
            if not fh.readline():  # skip line
                break
            name = fh.readline()[1:-1]
            range = fh.readline()[1:-1]
            if name.startswith("name:") and range.startswith("range:"):
                name = name[5:]
                range = range[6:].split("-")
            else:
                raise WrongFormat()

            ci.addChunk(name, (int(range[0]), int(range[1])))
        fh.close()
        return ci

    def remove(self):
        fs_name = fs_encode("%s.chunks" % self.name)
        if os.path.exists(fs_name):
            os.remove(fs_name)

    def getCount(self):
        return len(self.chunks)

    def getChunkName(self, index):
        return self.chunks[index][0]

    def getChunkRange(self, index):
        return self.chunks[index][1]


class HTTPChunk(HTTPRequest):
    def __init__(self, id, parent, range=None, resume=False):
        self.id = id
        self.p = parent  # HTTPDownload instance
        self.range = range  # tuple (start, end)
        self.resume = resume
        self.log = parent.log

        self.size = range[1] - range[0] if range else -1
        self.arrived = 0
        self.lastURL = self.p.referer

        self.aborted = False  # indicates that the chunk aborted gracefully

        self.c = pycurl.Curl()

        self.header = ""
        self.headerParsed = False  # indicates if the header has been processed

        self.fp = None  # file handle

        self.initHandle()
        self.setInterface(self.p.options)

        self.BOMChecked = False  # check and remove byte order mark

        self.rep = None

        self.sleep = 0.0
        self.lastSize = 0

    def __repr__(self):
        return "<HTTPChunk id=%d, size=%d, arrived=%d>" % (self.id, self.size, self.arrived)

    @property
    def cj(self):
        return self.p.cj

    def formatRange(self):
        if self.id == len(self.p.info.chunks) - 1:  # as last chunk dont set end range, so we get everything
            if self.resume:
                range = "%i-" % (self.arrived + self.range[0])
            else:
                range = "%i-" % self.range[0]
        else:
            if self.id == 0 and not self.resume:  # special case for first chunk
                range = "%i-%i" % (0, min(self.range[1] + 1, self.p.size - 1))
            else:
                range = "%i-%i" % (self.arrived + self.range[0], min(self.range[1] + 1, self.p.size - 1))

        return range

    def getHandle(self):
        """ returns a Curl handle ready to use for perform/multi-perform """

        self.setRequestContext(self.p.url, self.p.get, self.p.post, self.p.referer, self.p.cj)
        self.c.setopt(pycurl.WRITEFUNCTION, self.writeBody)
        self.c.setopt(pycurl.HEADERFUNCTION, self.writeHeader)

        # request all bytes, since some servers in russia seems to have a defect arihmetic unit

        fs_name = fs_encode(self.p.info.getChunkName(self.id))
        if self.resume:
            self.fp = open(fs_name, "ab")
            self.arrived = self.fp.tell()
            if not self.arrived:
                self.arrived = os.stat(fs_name).st_size

            if self.range:
                # do nothing if chunk already finished
                if self.arrived + self.range[0] >= self.range[1]:
                    return None

                range = self.formatRange()

                self.log.debug("Chunked resume with range %s" % self.formatRange())
                self.c.setopt(pycurl.RANGE, range)
            else:
                self.log.debug("Resume File from %i" % self.arrived)
                self.c.setopt(pycurl.RESUME_FROM, self.arrived)

        else:
            if self.range:
                range = self.formatRange()

                self.log.debug("Chunked with range %s" % range)
                self.c.setopt(pycurl.RANGE, range)

            self.fp = open(fs_name, "wb")

        return self.c

    def writeHeader(self, buf):
        self.header += buf
        # @TODO forward headers?, this is possibly unneeeded, when we just parse valid 200 headers
        # as first chunk, we will parse the headers
        if not self.range and self.header.endswith("\r\n\r\n"):
            self.parseHeader()
        elif not self.range and buf.startswith("150") and "data connection" in buf:  # ftp file size parsing
            size = re.search(r'(\d+) bytes', buf)
            if size:
                self.p.size = int(size.group(1))
                self.p.chunkSupport = True

        self.headerParsed = True

        return None  #: All is fine

    def writeBody(self, buf):
        #: Ignore BOM, it confuses unrar
        if not self.BOMChecked:
            if buf[:3] == codecs.BOM_UTF8:
                buf = buf[3:]
            self.BOMChecked = True

        size = len(buf)

        self.arrived += size

        self.fp.write(buf)

        if self.p.bucket:
            time.sleep(self.p.bucket.consumed(size))

        else:
            # Avoid small buffers, increasing sleep time slowly if buffer size gets smaller
            # otherwise reduce sleep time percentual (values are based on tests)
            # So in general cpu time is saved without reducing bandwith too much

            if size < self.lastSize:
                self.sleep += 0.002
            else:
                self.sleep *= 0.7

            self.lastSize = size

            time.sleep(self.sleep)

        if self.range and self.arrived > self.size:
            self.aborted = True  #: Tell parent to ignore the pycurl Exception
            return 0  #: Close if we have enough data

        return None  #: All is fine

    def parseHeader(self):
        """parse data from recieved header"""
        for orgline in self.header.splitlines():
            line = orgline.strip().lower()
            if line.startswith("accept-ranges") and "bytes" in line:
                self.p.chunkSupport = True

            elif line.startswith("content-disposition"):
                disposition_value = orgline.split(":", 1)[1].strip()
                disposition_type, disposition_params = parse_header(disposition_value)

                fname = None
                if 'filename*' in disposition_params:
                    fname = disposition_params['filename*']
                    m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', fname, re.I)  #: rfc2047
                    if m is not None:
                        fname, enc = decode_header(fname)[0]
                        try:
                            fname = fname.decode(enc)
                        except LookupError:
                            self.log.warning("Content-Disposition: | error: No decoder found for %s" % enc)
                            fname = None
                        except UnicodeEncodeError:
                            self.log.warning("Content-Disposition: | error: Error when decoding string from %s." % enc)
                            fname = None

                    else:
                        m = re.search(r'(.+?)\'(.*)\'(.+)', fname)
                        if m is not None:
                            enc, lang, data = m.groups()
                            try:
                                fname = urllib.unquote(data).decode(enc)
                            except LookupError:
                                self.log.warning("Content-Disposition: | error: No decoder found for %s" % enc)
                                fname = None
                            except UnicodeEncodeError:
                                self.log.warning("Content-Disposition: | error: Error when decoding string from %s." % enc)
                                fname = None

                        else:
                            fname = None

                if fname is None:
                    if 'filename' in disposition_params:
                        fname = disposition_params['filename']
                        m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', fname, re.I)  #: rfc2047
                        if m is not None:
                            fname, enc = decode_header(m.group(0))[0]
                            try:
                                fname = fname.decode(enc)
                            except LookupError:
                                self.log.warning("Content-Disposition: | error: No decoder found for %s" % enc)
                                continue
                            except UnicodeEncodeError:
                                self.log.warning("Content-Disposition: | error: Error when decoding string from %s." % enc)
                                continue
                        else:
                            try:
                                fname = urllib.unquote(fname).decode('iso-8859-1')
                            except UnicodeEncodeError:
                                self.log.warning("Content-Disposition: | error: Error when decoding string from iso-8859-1.")
                                continue
                    else:
                        continue

                    #: Drop unsafe characters
                    fname = posixpath_basename(fname)
                    fname = ntpath_basename(fname)
                    for badc in '<>:"/\\|?*\0':
                        fname = fname.replace(badc, "")
                    fname = fname.lstrip('.')

                    self.log.debug("Content-Disposition: %s" % fname)
                    self.p.updateDisposition(fname)

            elif not self.resume and line.startswith("content-length"):
                self.p.size = int(line.split(":")[1])

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
        self.log.debug("Chunked with range %s" % self.formatRange())

    def flushFile(self):
        """  flush and close file """
        self.fp.flush()
        os.fsync(self.fp.fileno())  # make sure everything was written to disk
        self.fp.close()  # needs to be closed, or merging chunks will fail

    def close(self):
        """ closes everything, unusable after this """
        if self.fp: self.fp.close()
        self.c.close()
        if hasattr(self, "p"): del self.p
