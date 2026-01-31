# -*- coding: utf-8 -*-

import codecs
import os
import re
import time
import urllib.parse
from email.header import decode_header as parse_mime_header
from ntpath import basename as ntpath_basename
from posixpath import basename as posixpath_basename

import pycurl

from ...utils import parse, purge
from ...utils.web.parse import http_header as parse_header_line
from .http_headers import HttpHeaders
from .http_request import HTTPRequest


class WrongFormat(Exception):
    pass


class ChunkInfo:
    def __init__(self, name):
        self.name = os.fsdecode(name)
        self.size = 0
        self.resume = False
        self.chunks = []

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
        with open(fs_name, encoding="utf-8") as fh:
            name = fh.readline()[:-1]
            size = fh.readline()[:-1]
            if name.startswith("name:") and size.startswith("size:"):
                name = name[5:]
                size = size[5:]
            else:
                fh.close()
                raise WrongFormat
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
                if not fh.readline():  #: skip line
                    break
                name = fh.readline()[1:-1]
                range = fh.readline()[1:-1]
                if name.startswith("name:") and range.startswith("range:"):
                    name = name[5:]
                    range = range[6:].split("-")
                else:
                    raise WrongFormat

                if save_folder != os.path.dirname(name):
                    raise IOError

                ci.add_chunk(name, (int(range[0]), int(range[1])))

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


class HTTPChunk(HTTPRequest):
    def __init__(self, id, parent, range=None, resume=False):
        self.id = id
        self.p = parent  #: HTTPDownload instance
        self.range = range  #: tuple (start, end)
        self.resume = resume
        self.log = parent.log

        self.size = range[1] - range[0] if range else -1
        self.arrived = 0
        self.last_url = self.p.referer

        self.code = 0  #: last http code, set by parent

        self.aborted = False  # indicates that the chunk aborted gracefully

        self.c = pycurl.Curl()

        self._header_buffer = b""
        self._body_buffer = None

        self.request_headers = HttpHeaders()
        self.response_headers = HttpHeaders()

        self.fp = None  #: file handle

        self.ssl_aiachaser = False
        self.aia_cainfo = None

        self.init_handle()
        self.c.setopt(pycurl.ENCODING, None)  #: avoid pycurl error 61
        self.set_interface(self.p.options)

        self.BOMChecked = False  #: check and remove byte order mark

        self.sleep = 0.0
        self.last_size = 0

    def __repr__(self):
        return f"<HTTPChunk id={self.id}, size={self.size}, arrived={self.arrived}>"

    @property
    def cj(self):
        return self.p.cj

    def format_range(self):
        if self.id == len(self.p.info.chunks) - 1:  #: as last chunk don't set end range, so we get everything
            end = ""
            if self.resume:
                start = self.arrived + self.range[0]
            else:
                start = self.range[0]
        else:
            end = min(self.range[1] + 1, self.p.size - 1)
            if self.id == 0 and not self.resume:  #: special case for first chunk
                start = 0
            else:
                start = self.arrived + self.range[0]

        return f"{start}-{end}"

    def get_handle(self):
        """
        returns a Curl handle ready to use for perform/multiperform.
        """
        self.set_request_context(
            self.p.url, self.p.get, self.p.post, self.p.referer, self.p.cj
        )
        self.c.setopt(pycurl.WRITEFUNCTION, self._write_body_callback)
        self.c.setopt(pycurl.HEADERFUNCTION, self._write_header_callback)

        # request all bytes, since some servers in russia seems to have a defect
        # arithmetic unit

        fs_name = self.p.info.get_chunk_filename(self.id)
        if self.resume:
            if not os.path.exists(fs_name):
                raise pycurl.error(33)  #: simulate cannot resume
            self.fp = open(fs_name, mode="ab")
            self.arrived = self.fp.tell()
            if not self.arrived:
                self.arrived = os.stat(fs_name).st_size

            if self.range:
                #: do nothing if chunk already finished
                if self.arrived + self.range[0] >= self.range[1]:
                    return None

                range = self.format_range()

                self.log.debug(f"Chunk {self.id + 1} chunked with range {range}")
                self.c.setopt(pycurl.RANGE, range)
            else:
                self.log.debug(f"Resume File from {self.arrived}")
                self.c.setopt(pycurl.RESUME_FROM, self.arrived)

        else:
            if self.range:
                range = self.format_range()

                self.log.debug(f"Chunk {self.id + 1} chunked with range {range}")
                self.c.setopt(pycurl.RANGE, range)

            self.fp = open(fs_name, mode="wb")

        return self.c

    def _write_header_callback(self, buf):
        self._header_buffer += buf
        # TODO: forward headers?, this is possibly unneeded, when we just parse valid 200 headers
        # as first chunk, we will parse the headers
        if not self.range and self._header_buffer.endswith(b"\r\n\r\n"):
            self.parse_header()
        #: FTP file size parsing
        elif not self.range and buf.startswith(b"150") and b"data connection" in buf:
            size = re.search(rb"(\d+) bytes", buf)
            if size:
                self.p.size = int(size.group(1))
                self.p.chunk_support = True

    def _write_body_callback(self, buf):
        #: ignore BOM, it confuses unrar
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
            # So in general cpu time is saved without reducing bandwidth too much

            if size < self.last_size:
                self.sleep += 0.002
            else:
                self.sleep *= 0.7

            self.last_size = size

            time.sleep(self.sleep)

        if self.range and self.arrived > self.size:
            self.aborted = True  #: tell parent to ignore the pycurl Exception
            return 0  #: close if chunk has enough data

    def parse_header(self):
        """
        parse data from received header.
        """
        self.response_headers.parse(self._header_buffer)

        self.p.chunk_support = self.response_headers.get("Accept-Ranges", "").lower() == "bytes"
        location = self.response_headers.get("Location")
        content_len = self.response_headers.get("Content-Length")
        if not self.resume and content_len:
            self.p.size = int(content_len)

        disposition_value = self.response_headers.get("Content-Disposition")
        if disposition_value:
            disposition_type, disposition_params = parse_header_line(disposition_value)

            fname = None
            if 'filename*' in disposition_params:
                fname = disposition_params['filename*']
                m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', fname, re.I)  #: rfc2047
                if m is not None:
                    data, encoding = parse_mime_header(fname)[0]
                    try:
                        fname = data.decode(encoding)
                    except LookupError:
                        self.log.warning(f"Content-Disposition: | error: No decoder found for {encoding}")
                        fname = None
                    except UnicodeEncodeError:
                        self.log.warning(f"Content-Disposition: | error: Error when decoding string from {encoding}")
                        fname = None

                else:
                    m = re.search(r'(.+?)\'(.*)\'(.+)', fname)
                    if m is not None:
                        encoding, lang, data = m.groups()
                        try:
                            fname = urllib.parse.unquote(data, encoding=encoding, errors="strict")
                        except LookupError:
                            self.log.warning(f"Content-Disposition: | error: No decoder found for {encoding}")
                            fname = None
                        except UnicodeDecodeError:
                            self.log.warning(f"Content-Disposition: | error: Error when decoding string from {encoding}")
                            fname = None

                    else:
                        fname = None

            if fname is None:
                if 'filename' in disposition_params:
                    fname = disposition_params['filename']
                    m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', fname, re.I)  #: rfc2047
                    if m is not None:
                        data, encoding = parse_mime_header(m.group(0))[0]
                        try:
                            fname = data.decode(encoding)
                        except LookupError:
                            fname = None
                            self.log.warning(f"Content-Disposition: | error: No decoder found for {encoding}")
                        except UnicodeEncodeError:
                            fname = None
                            self.log.warning(f"Content-Disposition: | error: Error when decoding string from {encoding}")
                    else:
                        try:
                            fname = urllib.parse.unquote(fname, encoding="iso-8859-1", errors="strict")
                        except UnicodeDecodeError:
                            fname = None
                            self.log.warning("Content-Disposition: | error: Error when decoding string from iso-8859-1.")

                elif disposition_type.lower() == "attachment":
                    if location is not None:
                        fname = parse.name(location)
                    else:
                        fname = parse.name(self.p.url)

            if fname is not None:
                #: Drop unsafe characters
                fname = posixpath_basename(fname)
                fname = ntpath_basename(fname)
                fname = purge.name(fname, sep="")
                fname = fname.lstrip('.')

                self.log.debug(f"Content-Disposition: {fname}")
                self.p.update_disposition(fname)

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
        self.log.debug("Chunk {id} chunked with range {range}".format(id=self.id + 1, range=self.format_range()))

    def flush_file(self):
        """
        flush and close file.
        """
        self.fp.flush()
        os.fsync(self.fp.fileno())  #: make sure everything was written to disk
        self.fp.close()  #: needs to be closed, or merging chunks will fail

    def close(self):
        """
        closes everything, unusable after this.
        """
        if self.aia_cainfo:
            os.remove(self.aia_cainfo)
            self.aia_cainfo = None
        if self.fp:
            self.fp.close()
        self.c.close()
        if hasattr(self, "p"):
            del self.p
