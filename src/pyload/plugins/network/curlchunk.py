# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals
from future import standard_library

import io
import os
import re
import time
from builtins import int, object, range

import pycurl
from pyload.utils import format
from pyload.utils.path import remove
from pyload.utils.struct import HeaderDict

from .curlrequest import CurlRequest

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

_re_filename = re.compile(
    r'filename(?P<type>=|\*=(?P<enc>.+)\'\')(?P<name>.*)',
    flags=re.I)


class CurlChunk(CurlRequest):

    def __init__(self, id, parent, range=None, resume=False):
        self.set_context(*parent.get_context())

        self.id = id
        self.p = parent  #: CurlDownload instance
        self.range = range  #: tuple (start, end)
        self.resume = resume
        self.log = parent.log

        self.size = range[1] - range[0] if range else -1
        self.arrived = 0
        self.last_url = self.p.referer

        self.c = pycurl.Curl()

        self.header = ""
        self.header_parsed = False  #: indicates if the header has been processed
        self.headers = HeaderDict()

        self.fp = None  #: file handle

        self.init_context()

        self.BOMChecked = False  #: check and remove byte order mark

        self.rep = None

        self.sleep = 0.000
        self.last_size = 0
        # next to last size
        self.n_last_size = 0

    def __repr__(self):
        return "<CurlChunk id={0:d}, size={1:d}, arrived={2:d}>".format(
            self.id, self.size, self.arrived)

    @property
    def cj(self):
        return self.p.context

    def get_handle(self):
        """
        Returns a Curl handle ready to use for perform/multiperform.
        """
        self.set_request_context(
            self.p.url, self.p.get, self.p.post, self.p.referer, self.p.cookies)
        self.c.setopt(pycurl.WRITEFUNCTION, self.write_body)
        self.c.setopt(pycurl.HEADERFUNCTION, self.write_header)

        # request all bytes, since some servers in russia seems to have a
        # defect arihmetic unit

        fs_name = format.path(self.p.info.get_chunk_name(self.id))
        if self.resume:
            self.fp = io.open(fs_name, mode='ab')
            self.arrived = self.fp.tell()
            if not self.arrived:
                self.arrived = os.stat(fs_name).st_size

            if self.range:
                # do nothing if chunk already finished
                if self.arrived + self.range[0] >= self.range[1]:
                    return None

                # as last chunk dont set end range, so we get everything
                if self.id == len(self.p.info.chunks) - 1:
                    range = b'{0:d}-'.format(self.arrived + self.range[0])
                else:
                    range = b'{0:d}-{1:d}'.format(self.arrived + self.range[
                                                0], min(self.range[1] + 1, self.p.size - 1))

                self.log.debug("Chunked resume with range {0}".format(range))
                self.c.setopt(pycurl.RANGE, range)
            else:
                self.log.debug("Resume File from {0:d}".format(self.arrived))
                self.c.setopt(pycurl.RESUME_FROM, self.arrived)

        else:
            if self.range:
                if self.id == len(self.p.info.chunks) - 1:  #: see above
                    range = "{0:d}-".format(self.range[0])
                else:
                    range = "{0:d}-{1:d}".format(self.range[0],
                                               min(self.range[1] + 1, self.p.size - 1))

                self.log.debug("Chunked with range {0}".format(range))
                self.c.setopt(pycurl.RANGE, range)

            self.fp = io.open(fs_name, mode='wb')

        return self.c

    def write_header(self, buf):
        self.header += buf
        # TODO: forward headers?, this is possibly unneeded, when we just parse valid 200 headers
        # as first chunk, we will parse the headers
        if not self.range and self.header.endswith("\r\n\r\n"):
            self.parse_header()
        # ftp file size parsing
        elif not self.range and buf.startswith("150") and "data connection" in buf:
            size = re.search(r"(\d+) bytes", buf)
            if size:
                self.p._size = int(size.group(1))
                self.p.chunk_support = True

        self.header_parsed = True

    def write_body(self, buf):
        # ignore BOM, it confuses unrar
        if not self.BOMChecked:
            if [ord(b) for b in buf[:3]] == [239, 187, 191]:
                buf = buf[3:]
            self.BOMChecked = True

        size = len(buf)
        self.n_last_size = self.last_size
        self.last_size = size

        self.arrived += size

        self.fp.write(buf)

        if self.p.bucket:
            time.sleep(self.p.bucket.consumed(size))

        # if the buffer sizes are stable no sleep will be made
        elif size != self.last_size or size != self.n_last_size:
            # Avoid small buffers, increasing sleep time slowly if buffer size gets smaller
            # otherwise reduce sleep time percentile (values are based on tests)
            # So in general cpu time is saved without reducing bandwidth too
            # much

            if size < self.last_size:
                self.sleep += 0.002
            else:
                self.sleep *= 0.7

            time.sleep(self.sleep)

        if self.range and self.arrived > self.size:
            return 0  #: close if we have enough data

    def parse_header(self):
        """
        Parse data from received header.
        """
        for orgline in self.decode_response(self.header).splitlines():
            line = orgline.strip().lower()
            if line.startswith("accept-ranges") and "bytes" in line:
                self.p.chunk_support = True

            if "content-disposition" in line:

                m = _re_filename.search(orgline.strip())
                if m:
                    name = format.name(m.groupdict()['name'])
                    self.p._name = name
                    self.log.debug("Content-Disposition: {0}".format(name))

            if not self.resume and line.startswith("content-length"):
                self.p._size = int(line.split(":")[1])

        self.header_parsed = True

    def stop(self):
        """
        The download will not proceed after next call of write_body.
        """
        self.range = [0, 0]
        self.size = 0

    def reset_range(self):
        """
        Reset the range, so the download will load all data available.
        """
        self.range = None

    def set_range(self, range):
        self.range = range
        self.size = range[1] - range[0]

    def flush_file(self):
        """
        Flush and close file.
        """
        self.fp.flush()
        os.fsync(self.fp.fileno())  #: make sure everything was written to disk
        self.fp.close()  #: needs to be closed, or merging chunks will fail

    def close(self):
        """
        Closes everything, unusable after this.
        """
        if self.fp:
            self.fp.close()
        self.c.close()
        if hasattr(self, "p"):
            del self.p
