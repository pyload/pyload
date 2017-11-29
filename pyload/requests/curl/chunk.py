# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import io
import os
import re
import time
from contextlib import closing

from future import standard_library
from future.builtins import int

import pycurl
from pyload.requests.curl.request import CurlRequest
from pyload.utils import purge
from pyload.utils.convert import to_str
from pyload.utils.struct import HeaderDict

standard_library.install_aliases()


class CurlChunk(CurlRequest):

    _RE_FILENAME = re.compile(
        r'filename(?P<type>=|\*=(?P<enc>.+)\'\')(?P<name>.*)',
        flags=re.I)

    # NOTE: Don't init CurlRequest
    def __init__(self, id, parent, range=None, resume=False):
        self.set_context(*parent.get_context())

        self.id = id
        self.p = parent  # CurlDownload instance
        self.range = range  # tuple (start, end)
        self.resume = resume
        self.log = parent.log

        self.size = range[1] - range[0] if range else - 1
        self.arrived = 0
        self.last_url = None

        self.curl = pycurl.Curl()

        self.header = ''
        # indicates if the header has been processed
        self.header_parsed = False
        self.headers = HeaderDict()

        self.fp = None  # file handle

        self.init_context()

        self.check_bom = True  # check and remove byte order mark

        self.rep = None

        self.sleep = 0.000
        self.last_size = 0
        # next to last size
        self._nlast_size = 0

    def __repr__(self):
        return '<CurlChunk id={0:d}, size={1:d}, arrived={2:d}>'.format(
            self.id, self.size, self.arrived)

    @property
    def cj(self):
        return self.p.context

    def get_handle(self):
        """Returns a Curl handle ready to use for perform/multiperform."""
        self.set_request_context(
            self.p.url, self.p.get, self.p.post,
            self.p.referer, self.p.cookies)
        self.setopt(pycurl.WRITEFUNCTION, self.write_body)
        self.setopt(pycurl.HEADERFUNCTION, self.write_header)

        try:
            self.fp.close()
        except AttributeError:
            pass

        # request all bytes, since some servers in russia seems to have a
        # defect arihmetic unit
        filename = self.p.info.get_chunk_name(self.id)
        if self.resume:
            self.fp = io.open(filename, mode='ab')
            self.arrived = self.fp.tell()
            if not self.arrived:
                self.arrived = os.stat(filename).st_size

            if self.range:
                # do nothing if chunk already finished
                if self.arrived + self.range[0] >= self.range[1]:
                    return

                # as last chunk dont set end range, so we get everything
                if self.id == len(self.p.info.chunks) - 1:
                    range = '{0:d}-'.format(self.arrived + self.range[0])
                else:
                    range = '{0:d}-{1:d}'.format(
                        self.arrived + self.range[0],
                        min(self.range[1] + 1, self.p.size - 1))

                self.log.debug('Chunked resume with range {0}'.format(range))
                self.setopt(pycurl.RANGE, range)
            else:
                self.log.debug('Resume File from {0:d}'.format(self.arrived))
                self.setopt(pycurl.RESUME_FROM, self.arrived)

        else:
            if self.range:
                if self.id == len(self.p.info.chunks) - 1:  # see above
                    range = '{0:d}-'.format(self.range[0])
                else:
                    range = '{0:d}-{1:d}'.format(
                        self.range[0],
                        min(self.range[1] + 1, self.p.size - 1))

                self.log.debug('Chunked with range {0}'.format(range))
                self.setopt(pycurl.RANGE, range)

            self.fp = io.open(filename, mode='wb')

        return self.curl

    def write_header(self, buf):
        buf = to_str(buf) # everything uses buf as string, so a conversion is needed
        self.header += buf
        # TODO: forward headers?, this is possibly unneeded,
        # when we just parse valid 200 headers as first chunk,
        # we will parse the headers
        if not self.range and self.header.endswith(os.linesep * 2):
            self.parse_header()
        # ftp file size parsing
        elif (not self.range and buf.startswith('150') and
              'data connection' in buf):
            size = re.search(r"(\d+) bytes", buf)
            if size is not None:
                self.p._size = int(size.group(1))
                self.p.chunk_support = True

        self.header_parsed = True

    def write_body(self, buf):
        # ignore BOM, it confuses unrar
        if self.check_bom:
            if buf[:3] == b'\xef\xbb\xbf':
                buf = buf[3:]
            self.check_bom = False

        size = len(buf)
        self._nlast_size = self.last_size
        self.last_size = size

        self.arrived += size

        self.fp.write(buf)

        if self.p.bucket:
            time.sleep(self.p.bucket.consumed(size))

        # if the buffer sizes are stable no sleep will be made
        elif size != self.last_size or size != self._nlast_size:
            # Avoid small buffers, increasing sleep time slowly if buffer size
            # gets smaller otherwise reduce sleep time percentile (values are
            # based on tests)
            # So in general cpu time is saved without reducing bandwidth too
            # much

            if size < self.last_size:
                self.sleep += 0.002
            else:
                self.sleep *= 0.7

            time.sleep(self.sleep)

        if self.range and self.arrived > self.size:
            return 0  # close if we have enough data

    def parse_header(self):
        """Parse data from received header."""
        for orgline in self.decode_response(self.header).splitlines():
            line = orgline.strip().lower()
            if line.startswith('accept-ranges') and 'bytes' in line:
                self.p.chunk_support = True

            if 'content-disposition' in line:
                m = self._RE_FILENAME.search(orgline.strip())
                if m is not None:
                    name = purge.name(m.groupdict()['name'])
                    self.p._name = name
                    self.log.debug('Content-Disposition: {0}'.format(name))

            if not self.resume and line.startswith('content-length'):
                self.p._size = int(line.split(':')[1])

        self.header_parsed = True

    def stop(self):
        """The download will not proceed after next call of write_body."""
        self.range = [0, 0]
        self.size = 0

    def reset_range(self):
        """Reset the range, so the download will load all data available."""
        self.range = None

    def set_range(self, range):
        self.range = range
        self.size = range[1] - range[0]

    def flush_file(self):
        """Flush and close file."""
        # needs to be closed, or merging chunks will fail
        with closing(self.fp) as fp:
            fp.flush()
            os.fsync(fp.fileno())  # make sure everything was written to disk

    def close(self):
        """Closes everything, unusable after this."""
        try:
            self.fp.close()
        except AttributeError:
            pass
        self.curl.close()
        if hasattr(self, 'p'):
            del self.p
