# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import shutil
import time
from builtins import object, range, str
from logging import getLogger

import pycurl
from pyload.plugins.plugin import Abort

from ...utils.utils import fs_encode
from .http_chunk import ChunkInfo, HTTPChunk
from .http_request import BadHeader


class HTTPDownload(object):
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
        progressNotify=None,
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
        self.nameDisposition = None  #: will be parsed from content disposition

        self.chunks = []

        self.log = getLogger("pyload")

        try:
            self.info = ChunkInfo.load(filename)
            self.info.resume = True  #: resume is only possible with valid info file
            self.size = self.info.size
            self.infoSaved = True
        except IOError:
            self.info = ChunkInfo(filename)

        self.chunkSupport = None
        self.m = self.manager = pycurl.CurlMulti()

        # needed for speed calculation
        self.lastArrived = []
        self.speeds = []
        self.lastSpeeds = [0, 0]

        self.progressNotify = progressNotify

    @property
    def speed(self):
        last = [sum(x) for x in self.lastSpeeds if x]
        return (sum(self.speeds) + sum(last)) // (1 + len(last))

    @property
    def arrived(self):
        return sum(c.arrived for c in self.chunks)

    @property
    def percent(self):
        if not self.size:
            return 0
        return (self.arrived * 100) // self.size

    def _copyChunks(self):
        init = fs_encode(self.info.getChunkName(0))  #: initial chunk name

        if self.info.getCount() > 1:
            with open(init, mode="rb+") as fo:  #: first chunkfile
                for i in range(1, self.info.getCount()):
                    # input file
                    # seek to beginning of chunk, to get rid of overlapping chunks
                    fo.seek(self.info.getChunkRange(i - 1)[1] + 1)
                    fname = fs_encode("{}.chunk{}".format(self.filename, i))
                    with open(fname, mode="rb") as fi:
                        buf = 32 << 10
                        while True:  #: copy in chunks, consumes less memory
                            data = fi.read(buf)
                            if not data:
                                break
                            fo.write(data)
                    if fo.tell() < self.info.getChunkRange(i)[1]:
                        fo.close()
                        os.remove(init)
                        self.info.remove()  #: there are probably invalid chunks
                        raise Exception(
                            "Downloaded content was smaller than expected. Try to reduce download connections."
                        )
                    os.remove(fname)  #: os.remove chunk

        if self.nameDisposition and self.disposition:
            self.filename = os.path.join(
                os.path.dirname(self.filename), self.nameDisposition
            )

        shutil.move(init, fs_encode(self.filename))
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
                    self.closeChunk(chunk)

                return self._download(chunks, False)
            else:
                raise
        finally:
            self.close()

        if self.nameDisposition and self.disposition:
            return self.nameDisposition
        return None

    def _download(self, chunks, resume):
        if not resume:
            self.info.clear()
            self.info.addChunk(
                "{}.chunk0".format(self.filename), (0, 0)
            )  #: create an initial entry)

        self.chunks = []

        # initial chunk that will load complete file (if needed)
        init = HTTPChunk(0, self, None, resume)

        self.chunks.append(init)
        self.m.add_handle(init.getHandle())

        lastFinishCheck = 0
        lastTimeCheck = 0
        chunksDone = set()  #: list of curl handles that are finished
        chunksCreated = False
        done = False
        if (
            self.info.getCount() > 1
        ):  #: This is a resume, if we were chunked originally assume still can
            self.chunkSupport = True

        while True:
            # need to create chunks
            if (
                not chunksCreated and self.chunkSupport and self.size
            ):  #: will be setted later by first chunk

                if not resume:
                    self.info.setSize(self.size)
                    self.info.createChunks(chunks)
                    self.info.save()

                chunks = self.info.getCount()

                init.setRange(self.info.getChunkRange(0))

                for i in range(1, chunks):
                    c = HTTPChunk(i, self, self.info.getChunkRange(i), resume)

                    handle = c.getHandle()
                    if handle:
                        self.chunks.append(c)
                        self.m.add_handle(handle)
                    else:
                        # close immediatly
                        self.log.debug("Invalid curl handle -> closed")
                        c.close()

                chunksCreated = True

            while True:
                ret, num_handles = self.m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            t = time.time()

            # reduce these calls
            while lastFinishCheck + 0.5 < t:
                # list of failed curl handles
                failed = []
                ex = None  #: save only last exception, we can only raise one anyway

                num_q, ok_list, err_list = self.m.info_read()
                for c in ok_list:
                    chunk = self.findChunk(c)
                    try:  #: check if the header implies success, else add it to failed list
                        chunk.verifyHeader()
                    except BadHeader as exc:
                        self.log.debug("Chunk {} failed: {}".format(chunk.id + 1, exc))
                        failed.append(chunk)
                        ex = exc
                    else:
                        chunksDone.add(c)

                for c in err_list:
                    curl, errno, msg = c
                    chunk = self.findChunk(curl)
                    # test if chunk was finished
                    if errno != 23 or "0 !=" not in msg:
                        failed.append(chunk)
                        ex = pycurl.error(errno, msg)
                        self.log.debug(
                            "Chunk {} failed: {}".format(chunk.id + 1, str(ex))
                        )
                        continue

                    try:  #: check if the header implies success, else add it to failed list
                        chunk.verifyHeader()
                    except BadHeader as exc:
                        self.log.debug("Chunk {} failed: {}".format(chunk.id + 1, exc))
                        failed.append(chunk)
                        ex = exc
                    else:
                        chunksDone.add(curl)
                if not num_q:  #: no more infos to get

                    # check if init is not finished so we reset download connections
                    # note that other chunks are closed and downloaded with init too
                    if failed and init not in failed and init.c not in chunksDone:
                        self.log.error(
                            "Download chunks failed, fallback to single connection | {}".format(
                                str(ex)
                            )
                        )

                        # list of chunks to clean and os.remove
                        to_clean = [x for x in self.chunks if x is not init]
                        for chunk in to_clean:
                            self.closeChunk(chunk)
                            self.chunks.remove(chunk)
                            os.remove(fs_encode(self.info.getChunkName(chunk.id)))

                        # let first chunk load the rest and update the info file
                        init.resetRange()
                        self.info.clear()
                        self.info.addChunk(
                            "{}.chunk0".format(self.filename), (0, self.size)
                        )
                        self.info.save()
                    elif failed:
                        raise ex or Exception

                    lastFinishCheck = t

                    if len(chunksDone) >= len(self.chunks):
                        if len(chunksDone) > len(self.chunks):
                            self.log.warning(
                                "Finished download chunks size incorrect, please report bug."
                            )
                        done = True  #: all chunks loaded

                    break

            if done:
                break  #: all chunks loaded

            # calc speed once per second, averaging over 3 seconds
            if lastTimeCheck + 1 < t:
                diff = [
                    c.arrived
                    - (self.lastArrived[i] if len(self.lastArrived) > i else 0)
                    for i, c in enumerate(self.chunks)
                ]

                self.lastSpeeds[1] = self.lastSpeeds[0]
                self.lastSpeeds[0] = self.speeds
                self.speeds = [float(a) / (t - lastTimeCheck) for a in diff]
                self.lastArrived = [c.arrived for c in self.chunks]
                lastTimeCheck = t
                self.updateProgress()

            if self.abort:
                raise Abort

            # time.sleep(0.003) #supress busy waiting - limits dl speed to  (1 / x) *
            # buffersize
            self.m.select(1)

        for chunk in self.chunks:
            chunk.flushFile()  #: make sure downloads are written to disk

        self._copyChunks()

    def updateProgress(self):
        if self.progressNotify:
            self.progressNotify(self.percent)

    def findChunk(self, handle):
        """
        linear search to find a chunk (should be ok since chunk size is usually
        low)
        """
        for chunk in self.chunks:
            if chunk.c == handle:
                return chunk

    def closeChunk(self, chunk):
        try:
            self.m.remove_handle(chunk.c)
        except pycurl.error as exc:
            self.log.debug("Error removing chunk: {}".format(exc))
        finally:
            chunk.close()

    def close(self):
        """
        cleanup.
        """
        for chunk in self.chunks:
            self.closeChunk(chunk)

        self.chunks = []
        if hasattr(self, "m"):
            self.m.close()
            del self.m
        if hasattr(self, "cj"):
            del self.cj
        if hasattr(self, "info"):
            del self.info
