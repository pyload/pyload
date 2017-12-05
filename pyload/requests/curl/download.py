# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import io
import os
import shutil
import sys
import time
from contextlib import closing

from future import standard_library
from future.builtins import range

import pycurl
from pyload.requests.base.download import DownloadRequest
from pyload.requests.base.request import Abort, ResponseException
from pyload.requests.chunk import ChunkInfo
from pyload.requests.cookie import CookieJar
from pyload.requests.curl.chunk import CurlChunk
from pyload.requests.types import Connection
from pyload.utils import purge
from pyload.utils.fs import fullpath, remove

standard_library.install_aliases()


# TODO: save content-disposition for resuming
class CurlDownload(DownloadRequest):
    """Loads an url, http + ftp supported."""
    # def __init__(self, url, filename, get=None, post={}, referer=None, cj=None,
    #              bucket=None, options=None, disposition=False):

    CONTEXT_CLASS = CookieJar

    if os.name == 'nt':
        PATH_MAXLEN = 255
    elif sys.platform == 'darwin':
        PATH_MAXLEN = 1024
    else:
        PATH_MAXLEN = 4096

    def __init__(self, *args, **kwargs):
        super(CurlDownload, self).__init__(*args, **kwargs)

        self.path = None
        self.disposition = False

        self.chunks = []
        self.chunk_support = None

        self.manager = pycurl.CurlMulti()

        # needed for speed calculation
        self.last_arrived = []
        self.speeds = []
        self.last_speeds = [0, 0]

    def init_context(self):
        """Should be used to initialize everything from given context and
        options."""
        #TODO: What should we do here?
        pass

    @property
    def speed(self):
        last = [sum(x) for x in self.last_speeds if x]
        return (sum(self.speeds) + sum(last)) // (1 + len(last))

    @property
    def arrived(self):
        if not self.chunks:
            return self._size
        return sum(c.arrived for c in self.chunks)

    @property
    def name(self):
        return self._name if self.disposition else None

    def _copy_chunks(self):
        init = self.info.get_chunk_name(0)  # initial chunk name

        if self.info.get_count() > 1:
            with io.open(init, 'rb+') as fpo:  # first chunkfile
                for i in range(1, self.info.get_count()):
                    # input file
                    # seek to beginning of chunk,
                    # to get rid of overlapping chunks
                    fpo.seek(self.info.get_chunk_range(i - 1)[1] + 1)
                    filename = '{0}.chunk{1:d}'.format(self.path, i)
                    buf = 32 << 10
                    with io.open(filename, mode='rb') as fpi:
                        while True:  # copy in chunks, consumes less memory
                            data = fpi.read(buf)
                            if not data:
                                break
                            fpo.write(data)

                    if fpo.tell() < self.info.get_chunk_range(i)[1]:
                        remove(init)
                        self.info.remove()  # there are probably invalid chunks
                        raise Exception(
                            'Downloaded content was smaller than expected')
                    remove(filename)  # remove chunk

        if self.name:
            filepath = os.path.join(os.path.dirname(self.path), self.name)
            self.set_path(filepath)

        shutil.move(init, self.path)

    def check_resume(self):
        try:
            self.info = ChunkInfo.load(self.path)
            # resume is only possible with valid info file
            self.info.resume = True
            self._size = self.info.size
            self.info_saved = True
        except IOError:
            self.info = ChunkInfo(self.path)

    def set_path(self, filepath):
        path = fullpath(filepath)
        dirname, filename = os.path.split(path)
        filename = purge.name(filename)

        overflow = len(os.path.join(dirname, filename)) - self.PATH_MAXLEN
        if overflow > 0:
            name, ext = os.path.splitext(filename)
            name = purge.truncate(name, overflow)
            filename = name + ext

        self.path = os.path.join(dirname, filename)

    def download(self, uri, filename, get=None, post=None, referer=True,
                 disposition=False, chunks=1, resume=False, cookies=True):
        """Returns new filename or None."""
        self.set_path(filename)

        self.url = uri
        self.disposition = disposition
        self.get = get or {}
        self.post = post or {}
        self.referer = referer
        self.cookies = cookies

        self.check_resume()
        chunks = max(1, chunks)
        resume = self.info.resume and resume

        try:
            self._download(chunks, resume)

        except pycurl.error as exc:
            # code 33 - no resume
            code = exc.args[0]
            if code == 33:
                # try again without resume
                self.log.debug('Errno 33 -> Restart without resume')

                # remove old handles
                for chunk in self.chunks:
                    self.close_chunk(chunk)

                return self._download(chunks, False)
            else:
                raise
        finally:
            self.close()

        return self.name

    def _download(self, chunks, resume):
        if not resume:
            self.info.clear()
            self.info.add_chunk('{0}.chunk0'.format(
                self.path), (0, 0))  # create an initial entry

        self.chunks = []

        # initial chunk that will load complete file (if needed)
        init = CurlChunk(0, self, None, resume)

        self.chunks.append(init)
        self.manager.add_handle(init.get_handle())

        last_finish_check = 0
        last_time_check = 0
        chunks_done = set()  # list of curl handles that are finished
        chunks_created = False
        done = False
        # This is a resume, if we were chunked originally assume still can
        if self.info.get_count() > 1:
            self.chunk_support = True

        while True:
            # need to create chunks
            # will be set later by first chunk
            if not chunks_created and self.chunk_support and self.size:

                self.flags ^= Connection.Resumable  # TODO: Recheck...
                if not resume:
                    self.info.set_size(self.size)
                    self.info.create_chunks(chunks)
                    self.info.save()

                chunks = self.info.get_count()

                init.set_range(self.info.get_chunk_range(0))

                for i in range(1, chunks):
                    c = CurlChunk(
                        i, self, self.info.get_chunk_range(i), resume)

                    handle = c.get_handle()
                    if handle:
                        self.chunks.append(c)
                        self.manager.add_handle(handle)
                    else:
                        # close immediately
                        self.log.debug('Invalid curl handle -> closed')
                        c.close()

                chunks_created = True

            while True:
                ret, _ = self.manager.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            t = time.time()

            # reduce these calls
            # when num_q is 0, the loop is exited
            while last_finish_check + 0.5 < t:
                # list of failed curl handles
                failed = []

                # TODO: Rewrite...
                # save only last exception, we can only raise one anyway
                exc = Exception()

                num_q, ok_list, err_list = self.manager.info_read()
                for c in ok_list:
                    chunk = self.find_chunk(c)
                    # check if the header implies success,
                    # else add it to failed list
                    try:
                        chunk.verify_header()
                    except ResponseException as exc:
                        self.log.debug(
                            'Chunk {0:d} failed'.format(
                                chunk.id + 1))
                        self.log.debug(exc, exc_info=True)
                        failed.append(chunk)
                    else:
                        chunks_done.add(c)

                for c in err_list:
                    curl, errno, msg = c
                    chunk = self.find_chunk(curl)
                    # test if chunk was finished
                    if errno != 23 or '0 !=' not in msg:
                        failed.append(chunk)
                        exc = pycurl.error(errno, msg)
                        self.log.debug(
                            'Chunk {0:d} failed'.format(chunk.id + 1))
                        self.log.debug(exc, exc_info=True)
                        continue
                    # check if the header implies success,
                    # else add it to failed list
                    try:
                        chunk.verify_header()
                    except ResponseException as exc:
                        self.log.debug(
                            'Chunk {0:d} failed'.format(
                                chunk.id + 1))
                        self.log.debug(exc, exc_info=True)
                        failed.append(chunk)
                    else:
                        chunks_done.add(curl)
                if not num_q:  # no more info to get

                    # check if init is not finished so we reset download
                    # connections
                    # note that other chunks are closed and everything
                    # downloaded with initial connection
                    if failed:
                        if init in failed or init.curl in chunks_done:
                            raise exc
                        self.log.error(
                            'Download chunks failed, fallback to '
                            'single connection | {0}'.format(exc))

                        # list of chunks to clean and remove
                        to_clean = [x for x in self.chunks if x is not init]
                        for chunk in to_clean:
                            self.close_chunk(chunk)
                            self.chunks.remove(chunk)
                            remove(self.info.get_chunk_name(chunk.id))

                        # let first chunk load the rest and update the
                        # info file
                        init.reset_range()
                        self.info.clear()
                        self.info.add_chunk('{0}.chunk0'.format(
                            self.path), (0, self.size))
                        self.info.save()

                    last_finish_check = t

                    if len(chunks_done) >= len(self.chunks):
                        if len(chunks_done) > len(self.chunks):
                            self.log.warning(
                                'Finished download chunks size incorrect')
                        done = True  # all chunks loaded

                    break

            if done:
                break  # all chunks loaded

            # calc speed once per second, averaging over 3 seconds
            if last_time_check + 1 < t:
                len_la = len(self.last_arrived)
                diff = [c.arrived - (self.last_arrived[i] if len_la > i else 0)
                        for i, c in enumerate(self.chunks)]

                self.last_speeds[1] = self.last_speeds[0]
                self.last_speeds[0] = self.speeds
                self.speeds = [float(a) // (t - last_time_check) for a in diff]
                self.last_arrived = [c.arrived for c in self.chunks]
                last_time_check = t

            if self._abort:
                raise Abort

            self.manager.select(1)

        for chunk in self.chunks:
            chunk.flush_file()  # make sure downloads are written to disk

        self._copy_chunks()

    def find_chunk(self, handle):
        """Linear search to find a chunk (should be ok since chunk size is
        usually low)."""
        for chunk in self.chunks:
            if chunk.curl == handle:
                return chunk

    def close_chunk(self, chunk):
        try:
            self.manager.remove_handle(chunk.curl)

        except pycurl.error as exc:
            self.log.debug('Error removing chunk')
            self.log.debug(exc, exc_info=True)

        finally:
            chunk.close()

    def close(self):
        """Cleanup."""
        for chunk in self.chunks:
            self.close_chunk(chunk)

        # Workaround: pycurl segfaults when closing multi, that never had
        # any curl handles
        if hasattr(self, 'manager'):
            with closing(pycurl.Curl()) as c:
                self.manager.add_handle(c)
                self.manager.remove_handle(c)

        self.chunks = []
        if hasattr(self, 'manager'):
            self.manager.close()
            del self.manager
        if hasattr(self, 'info'):
            del self.info
