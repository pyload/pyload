import codecs
import os
import re
import time

import pycurl

from ...utils import web
from .exceptions import WrongFormat
from .http_request import HTTPRequest


class ChunkInfo:
    def __init__(self, name):
        self.name = os.fsdecode(name)
        self.size = 0
        self.resume = False
        self.chunks = []
        self.loaded = False

    def __repr__(self):
        ret = f"ChunkInfo: {self.name}, {self.size}\n"
        for i, c in enumerate(self.chunks):
            ret += f"{i}# {c[1]}\n"
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
            self.add_chunk(f"{self.name}.chunk{i}", (current, end))
            current += chunk_size + 1

    def save(self):
        fs_name = f"{self.name}.chunks"
        with open(fs_name, mode="w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"name:{self.name}\n")
            fh.write(f"size:{self.size}\n")
            for i, c in enumerate(self.chunks):
                fh.write(f"#{i}:\n")
                fh.write(f"\tname:{c[0]}\n")
                fh.write(f"\trange:{c[1][0]}-{c[1][1]}\n")

    @staticmethod
    def load(name):
        fs_name = f"{name}.chunks"
        if not os.path.exists(fs_name):
            raise IOError
        with open(fs_name, encoding="utf-8") as fp:
            name_line = fp.readline()[:-1]
            size_line = fp.readline()[:-1]
            if name_line.startswith("name:") and size_line.startswith("size:"):
                name = name_line[5:]
                size = size_line[5:]
            else:
                fp.close()
                raise WrongFormat()
            save_folder = os.path.dirname(name)
            if (
                not os.path.exists(save_folder)
                and not os.path.isdir(save_folder)
                or save_folder != os.path.dirname(fs_name)
            ):
                raise IOError
            ci = ChunkInfo(name)
            ci.loaded = True
            ci.set_size(size)
            while True:
                if not fp.readline():
                    break
                name_line = fp.readline()[1:-1]
                range_line = fp.readline()[1:-1]
                if name_line.startswith("name:") and range_line.startswith("range:"):
                    chunk_name = name_line[5:]
                    chunk_range = range_line[6:].split("-")
                else:
                    raise WrongFormat()

                if save_folder != os.path.dirname(chunk_name):
                    raise IOError

                ci.add_chunk(chunk_name, (int(chunk_range[0]), int(chunk_range[1])))

        return ci

    def remove(self):
        fs_name = f"{self.name}.chunks"
        if os.path.exists(fs_name):
            os.remove(fs_name)

    def get_count(self):
        return len(self.chunks)

    def get_chunk_filename(self, index):
        return self.chunks[index][0]

    def get_chunk_range(self, index):
        return self.chunks[index][1]


class HTTPChunk:
    def __init__(self, id, parent, range=None, resume=False):
        self.id = id
        self.p = parent  #: HTTPDownload instance
        self.range = range  #: tuple (start, end)
        self.resume = resume

        # Chunk-specific state
        self.size = range[1] - range[0] if range else -1
        self.arrived = 0
        self.last_url = self.p.referer
        self.code = 0  #: last http code, set by parent
        self.aborted = False
        self.fp = None  #: file handle
        self.BOMChecked = False

        # Speed calculation

        # Create wrapped HTTPRequest with parent's configuration
        self.request = HTTPRequest(cookies=self.p.cj, options=self.p.options)

        # Expose commonly used attributes from wrapped request
        self.c = self.request.c
        self.log = self.request.log

        # Chunk uses its own header buffer for parsing, but delegates to request's headers
        self._header_buffer = b""

        # Configure chunk-specific curl options
        self.c.setopt(pycurl.ENCODING, None)  #: avoid pycurl error 61

    def __repr__(self):
        return f"<HTTPChunk id={self.id}, size={self.size}, arrived={self.arrived}>"

    @property
    def cj(self):
        """Delegate to parent's cookie jar."""
        return self.p.cj

    @property
    def request_headers(self):
        """Delegate to wrapped request's headers."""
        return self.request.request_headers

    @property
    def response_headers(self):
        """Delegate to wrapped request's headers."""
        return self.request.response_headers

    def verify_header(self):
        return self.request.verify_header()

    def format_range(self):
        """Format HTTP Range header value for this chunk."""
        if self.id == len(self.p.info.chunks) - 1:
            end = ""
            start = self.arrived + self.range[0] if self.resume else self.range[0]
        else:
            end = min(self.range[1] + 1, self.p.size - 1)
            if self.id == 0 and not self.resume:
                start = 0
            else:
                start = self.arrived + self.range[0]
        return f"{start}-{end}"

    def get_handle(self):
        """
        Returns a configured Curl handle ready for perform/multiperform.
        """
        # Configure wrapped request for this transfer
        self.request.set_request_context(
            self.p.url, self.p.get, self.p.post, self.p.referer, self.p.cj
        )

        # Override with chunk-specific callbacks
        self.c.setopt(pycurl.WRITEFUNCTION, self._write_body_callback)
        self.c.setopt(pycurl.HEADERFUNCTION, self._write_header_callback)

        # Setup file I/O
        fs_name = self.p.info.get_chunk_filename(self.id)

        if self.resume:
            if not os.path.exists(fs_name):
                raise pycurl.error(33)  #: simulate cannot resume
            self.fp = open(fs_name, mode="ab")
            self.arrived = self.fp.tell() or os.stat(fs_name).st_size

            if self.range:
                if self.arrived + self.range[0] >= self.range[1]:
                    return None  #: chunk already finished

                range_str = self.format_range()
                self.log.debug(f"Chunk {self.id + 1} resuming with range {range_str}")
                self.c.setopt(pycurl.RANGE, range_str)
            else:
                self.log.debug(f"Resume File from {self.arrived}")
                self.c.setopt(pycurl.RESUME_FROM, self.arrived)
        else:
            if self.range:
                range_str = self.format_range()
                self.log.debug(f"Chunk {self.id + 1} starting with range {range_str}")
                self.c.setopt(pycurl.RANGE, range_str)
            self.fp = open(fs_name, mode="wb")

        return self.c

    def _write_header_callback(self, buf):
        """Handle incoming header data."""
        self._header_buffer += buf

        if not self.range and self._header_buffer.endswith(b"\r\n\r\n"):
            self.parse_header()
        elif not self.range and buf.startswith(b"150") and b"data connection" in buf:
            # FTP file size parsing
            size = re.search(rb"(\d+) bytes", buf)
            if size:
                self.p.size = int(size.group(1))
                self.p.chunk_support = True

    def _write_body_callback(self, buf):
        """Handle incoming body data with BOM stripping and rate limiting."""
        # Strip BOM on first chunk
        if not self.BOMChecked:
            if buf[:3] == codecs.BOM_UTF8:
                buf = buf[3:]
            self.BOMChecked = True

        size = len(buf)
        self.arrived += size
        self.fp.write(buf)

        # Rate limiting
        if self.p.bucket:
            time.sleep(self.p.bucket.consumed(size))

        # Check if chunk is complete
        if self.range and self.arrived > self.size:
            self.aborted = True
            return 0  #: close transfer

        return None  #: continue

    def parse_header(self):
        """Parse response headers and update parent state."""
        self.response_headers.parse(self._header_buffer)

        self.p.chunk_support = self.response_headers.get("Accept-Ranges", "").lower() == "bytes"

        if not self.resume:
            content_len = self.response_headers.get("Content-Length")
            if content_len:
                self.p.size = int(content_len)

        disposition_value = self.response_headers.get("Content-Disposition")
        if disposition_value:
            try:
                location = self.response_headers.get("Location")
                filename = web.parse.disposition(disposition_value, location, self.p.url)
                if filename:
                    self.log.debug(f"Content-Disposition: {filename}")
                    self.p.update_disposition(filename)
            except ValueError as exc:
                self.log.warning(exc)

    def stop(self):
        """Stop download after next write_body call."""
        self.range = [0, 0]
        self.size = 0

    def reset_range(self):
        """
        Reset the range, so the download will load all data available.
        """
        self.range = None

    def set_range(self, range):
        """Set a new byte range for this chunk."""
        self.range = range
        self.size = range[1] - range[0]
        self.log.debug(f"Chunk {self.id + 1} range set to {self.format_range()}")

    def flush_file(self):
        """Flush and close file handle."""
        if self.fp:
            self.fp.flush()
            os.fsync(self.fp.fileno())
            self.fp.close()

    def close(self):
        """Clean up resources."""
        if self.fp:
            self.fp.close()
            self.fp = None

        if self.request:
            self.request.close()
            self.request = None
            self.c = None

