# -*- coding: utf-8 -*-

import os
import shutil
import time
from logging import getLogger

import pycurl
from pyload import APPID

from ..exceptions import Abort
from .http_chunk import ChunkInfo, HTTPChunk
from .http_request import BadHeader


class HTTPDownload:
    """
    loads a url http + ftp.
    """

    def __init__(
        self,
        url,
        filename,
        get={},
        post={},
        referer=None,
        cj=None,
        bucket=None,
        options={},
        progress_notify=None,
        disposition=False,
    ):
        self.url = url
        self.filename = filename  #: complete file destination, not only name
        self.get = get
        self.post = post
        self.referer = referer
        self.cj = cj  #: cookiejar if cookies are needed
        self.bucket = bucket
        self.options = options
        self.disposition = disposition
        # all arguments

        self.abort = False
        self.size = 0
        self.name_disposition = None  #: will be parsed from content disposition

        self.chunks = []

        self.log = getLogger(APPID)

        try:
            self.info = ChunkInfo.load(filename)
            self.info.resume = True  #: resume is only possible with valid info file
            self.size = self.info.size
            self.info_saved = True
        except IOError:
            self.info = ChunkInfo(filename)

        self.chunk_support = None
        self.m = self.manager = pycurl.CurlMulti()

        # needed for speed calculation
        self.last_arrived = []
        self.speeds = []
        self.last_speeds = [0, 0]

        self.progress_notify = progress_notify

    @property
    def speed(self):
        last = [sum(x) for x in self.last_speeds if x]
        return (sum(self.speeds) + sum(last)) // (1 + len(last))

    @property
    def arrived(self):
        return sum(c.arrived for c in self.chunks)

    @property
    def percent(self):
        if not self.size:
            return 0
        return (self.arrived * 100) // self.size

    def _copy_chunks(self):
        init = self.info.get_chunk_name(0)  #: initial chunk name

        if self.info.get_count() > 1:
            with open(init, mode="rb+") as fo:  #: first chunkfile
                for i in range(1, self.info.get_count()):
                    # input file
                    # seek to beginning of chunk, to get rid of overlapping chunks
                    fo.seek(self.info.get_chunk_range(i - 1)[1] + 1)
                    fname = f"{self.filename}.chunk{i}"
                    with open(fname, mode="rb") as fi:
                        buf = 32 << 10
                        while True:  #: copy in chunks, consumes less memory
                            data = fi.read(buf)
                            if not data:
                                break
                            fo.write(data)
                    if fo.tell() < self.info.get_chunk_range(i)[1]:
                        fo.close()
                        os.remove(init)
                        self.info.remove()  #: there are probably invalid chunks
                        raise Exception(
                            "Downloaded content was smaller than expected. Try to reduce download connections."
                        )
                    os.remove(fname)  #: os.remove chunk

        if self.name_disposition and self.disposition:
            self.filename = os.path.join(
                os.path.dirname(self.filename), self.name_disposition
            )

        shutil.move(init, self.filename)
        self.info.remove()  #: os.remove info file

    def download(self, chunks=1, resume=False):
        """
        returns new filename or None.
        """
        chunks = max(1, chunks)
        resume = self.info.resume and resume

        try:
            self._download(chunks, resume)
        except pycurl.error as exc:
            # code 33 - no resume
            code = exc.args[0]
            if code == 33:
                # try again without resume
                self.log.debug("Errno 33 -> Restart without resume")

                # os.remove old handles
                for chunk in self.chunks:
                    self.close_chunk(chunk)

                return self._download(chunks, False)
            else:
                raise
        finally:
            self.close()

        if self.name_disposition and self.disposition:
            return self.name_disposition
        return None

    def _download(self, chunks, resume):
        if not resume:
            self.info.clear()
            self.info.add_chunk(
                f"{self.filename}.chunk0", (0, 0)
            )  #: create an initial entry)

        self.chunks = []

        # initial chunk that will load complete file (if needed)
        init = HTTPChunk(0, self, None, resume)

        self.chunks.append(init)
        self.m.add_handle(init.get_handle())

        last_finish_check = 0
        last_time_check = 0
        chunks_done = set()  #: list of curl handles that are finished
        chunks_created = False
        done = False
        if (
            self.info.get_count() > 1
        ):  #: This is a resume, if we were chunked originally assume still can
            self.chunk_support = True

        while True:
            # need to create chunks
            if (
                not chunks_created and self.chunk_support and self.size
            ):  #: will be setted later by first chunk

                if not resume:
                    self.info.set_size(self.size)
                    self.info.create_chunks(chunks)
                    self.info.save()

                chunks = self.info.get_count()

                init.set_range(self.info.get_chunk_range(0))

                for i in range(1, chunks):
                    c = HTTPChunk(i, self, self.info.get_chunk_range(i), resume)

                    handle = c.get_handle()
                    if handle:
                        self.chunks.append(c)
                        self.m.add_handle(handle)
                    else:
                        # close immediatly
                        self.log.debug("Invalid curl handle -> closed")
                        c.close()

                chunks_created = True

            while True:
                ret, num_handles = self.m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            t = time.time()

            # reduce these calls
            while last_finish_check + 0.5 < t:
                # list of failed curl handles
                failed = []
                ex = None  #: save only last exception, we can only raise one anyway

                num_q, ok_list, err_list = self.m.info_read()
                for c in ok_list:
                    chunk = self.find_chunk(c)
                    try:  #: check if the header implies success, else add it to failed list
                        chunk.verify_header()
                    except BadHeader as exc:
                        self.log.debug(f"Chunk {chunk.id + 1} failed: {exc}")
                        failed.append(chunk)
                        ex = exc
                    else:
                        chunks_done.add(c)

                for c in err_list:
                    curl, errno, msg = c
                    chunk = self.find_chunk(curl)
                    # test if chunk was finished
                    if errno != 23 or "0 !=" not in msg:
                        failed.append(chunk)
                        ex = pycurl.error(errno, msg)
                        self.log.debug(f"Chunk {chunk.id + 1} failed: {ex}")
                        continue

                    try:  #: check if the header implies success, else add it to failed list
                        chunk.verify_header()
                    except BadHeader as exc:
                        self.log.debug(f"Chunk {chunk.id + 1} failed: {exc}")
                        failed.append(chunk)
                        ex = exc
                    else:
                        chunks_done.add(curl)
                if not num_q:  #: no more infos to get

                    # check if init is not finished so we reset download connections
                    # note that other chunks are closed and downloaded with init too
                    if failed and init not in failed and init.c not in chunks_done:
                        self.log.error(
                            f"Download chunks failed, fallback to single connection | {ex}"
                        )

                        # list of chunks to clean and os.remove
                        to_clean = [x for x in self.chunks if x is not init]
                        for chunk in to_clean:
                            self.close_chunk(chunk)
                            self.chunks.remove(chunk)
                            os.remove(self.info.get_chunk_name(chunk.id))

                        # let first chunk load the rest and update the info file
                        init.reset_range()
                        self.info.clear()
                        self.info.add_chunk(f"{self.filename}.chunk0", (0, self.size))
                        self.info.save()
                    elif failed:
                        raise ex or Exception

                    last_finish_check = t

                    if len(chunks_done) >= len(self.chunks):
                        if len(chunks_done) > len(self.chunks):
                            self.log.warning(
                                "Finished download chunks size incorrect, please report bug."
                            )
                        done = True  #: all chunks loaded

                    break

            if done:
                break  #: all chunks loaded

            # calc speed once per second, averaging over 3 seconds
            if last_time_check + 1 < t:
                diff = [
                    c.arrived
                    - (self.last_arrived[i] if len(self.last_arrived) > i else 0)
                    for i, c in enumerate(self.chunks)
                ]

                self.last_speeds[1] = self.last_speeds[0]
                self.last_speeds[0] = self.speeds
                self.speeds = [float(a) / (t - last_time_check) for a in diff]
                self.last_arrived = [c.arrived for c in self.chunks]
                last_time_check = t
                self.update_progress()

            if self.abort:
                raise Abort

            # time.sleep(0.003) #supress busy waiting - limits dl speed to  (1 / x) *
            # buffersize
            self.m.select(1)

        for chunk in self.chunks:
            chunk.flush_file()  #: make sure downloads are written to disk

        self._copy_chunks()

    def update_progress(self):
        if self.progress_notify:
            self.progress_notify(self.percent)

    def find_chunk(self, handle):
        """
        linear search to find a chunk (should be ok since chunk size is usually low)
        """
        for chunk in self.chunks:
            if chunk.c == handle:
                return chunk

    def close_chunk(self, chunk):
        try:
            self.m.remove_handle(chunk.c)
        except pycurl.error as exc:
            self.log.debug(f"Error removing chunk: {exc}")
        finally:
            chunk.close()

    def close(self):
        """
        cleanup.
        """
        for chunk in self.chunks:
            self.close_chunk(chunk)

        self.chunks = []
        if hasattr(self, "m"):
            self.m.close()
            del self.m
        if hasattr(self, "cj"):
            del self.cj
        if hasattr(self, "info"):
            del self.info
