# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import re
import time
from builtins import int

from future import standard_library

from pyload.utils import purge
from pyload.utils.decorator import trycatch
from pyload.utils.struct.lock import RWLock, lock

from .init import (BaseObject, DownloadInfo, DownloadProgress, DownloadStatus,
                   ExceptionObject, MediaType, ProgressInfo, ProgressType)

try:
    from enum import IntEnum
except ImportError:
    from aenum import IntEnum

standard_library.install_aliases()


statusmap = {
    'none': 0,
    'offline': 1,
    'online': 2,
    'queued': 3,
    'paused': 4,
    'finished': 5,
    'skipped': 6,
    'failed': 7,
    'starting': 8,
    'waiting': 9,
    'downloading': 10,
    'temp. offline': 11,
    'aborted': 12,
    'not possible': 13,
    'missing': 14,
    'file mismatch': 15,
    'occupied': 16,
    'decrypting': 17,
    'processing': 18,
    'custom': 19,
    'unknown': 20
}
filetypes = {
    MediaType.Audio: re.compile(
        r'\.(m3u|m4a|mp3|wav|wma|aac?|flac|midi|m4b)$', flags=re.I),
    MediaType.Image: re.compile(
        r'\.(jpe?g|bmp|png|gif|ico|tiff?|svg|psd)$', flags=re.I),
    MediaType.Video: re.compile(
        r'\.(3gp|flv|m4v|avi|mp4|mov|swf|vob|wmv|divx|mpe?g|rm|mkv)$',
        flags=re.I),
    MediaType.Document: re.compile(
        r'\.(epub|mobi|acsm|azw[0-9]|pdf|txt|md|abw|docx?|tex|odt|rtf||log)$',
        flags=re.I),
    MediaType.Archive: re.compile(
        r'\.(rar|r[0-9]+|7z|7z.[0-9]+|zip|gz|bzip2?|tar|lzma)$', flags=re.I),
    MediaType.Executable: re.compile(
        r'\.(jar|exe|dmg|sh|apk)$', flags=re.I), }


def guess_type(name):
    for mt, regex in filetypes.items():
        if regex.search(name) is not None:
            return mt
    return MediaType.Other


class FileStatus(IntEnum):
    Ok = 0
    Missing = 1
    Remote = 2


class FileDoesNotExist(ExceptionObject):

    __slots__ = ['fid']

    def __init__(self, fid=None):
        self.fid = fid


class FileInfo(BaseObject):

    __slots__ = ['fid', 'name', 'package', 'owner', 'size',
                 'status', 'media', 'added', 'fileorder', 'download']

    def __init__(self, fid=None, name=None, package=None, owner=None,
                 size=None, status=None, media=None, added=None,
                 fileorder=None, download=None):
        self.fid = fid
        self.name = name
        self.package = package
        self.owner = owner
        self.size = size
        self.status = status
        self.media = media
        self.added = added
        self.fileorder = fileorder
        self.download = download


class File(BaseObject):
    """
    Represents a file object at runtime.
    """
    __slots__ = ['_name', '_size', 'abort', 'added', 'error', 'fid',
                 'fileorder', 'filestatus', 'hash', 'lock', 'manager', 'media',
                 'owner', 'packageid', 'plugin', 'pluginclass', 'pluginname',
                 'reconnected', 'status', 'statusname', 'url', 'wait_until']

    @staticmethod
    def from_info_data(m, info):
        file = File(m, info.fid, info.name, info.size, info.status, info.media,
                    info.added, info.fileorder, "", "", "", DownloadStatus.NA,
                    "", info.package, info.owner)
        if info.download:
            file.url = info.download.url
            file.pluginname = info.download.plugin
            file.hash = info.download.hash
            file.status = info.download.status
            file.error = info.download.error
        return file

    def __init__(
        self, manager, fid, name, size, filestatus, media, added,
            fileorder, url, pluginname, hash, status, error, package, owner):
        self.__manager = manager
        self.__pyload = manager.pyload_core

        self.fid = int(fid)
        self._name = purge.name(name)
        self._size = int(size)
        self.filestatus = filestatus
        self.media = media
        self.added = added
        self.fileorder = fileorder
        self.url = url
        self.pluginname = pluginname
        self.hash = hash
        self.status = status
        self.error = error
        self.owner = owner
        self.packageid = package
        # database information ends here

        self.lock = RWLock()

        self.plugin = None

        self.wait_until = 0  # time.time() + time to wait

        # status attributes
        self.abort = False
        self.reconnected = False
        self.statusname = None

    @property
    def pyload_core(self):
        return self.__pyload

    def get_size(self):
        """
        Get size of download.
        """
        if self.plugin.dl.size is not None:
            self.self._size(self.plugin.dl.size)
        return self._size

    # NOTE: convert size to int
    def set_size(self, value):
        self._size = int(value)

    size = property(get_size, set_size)

    def get_name(self):
        try:
            if self.plugin.req.name:
                return self.plugin.req.name
            else:
                return self._name
        except Exception:
            return self._name

    def set_name(self, name):
        """
        Only set unicode or utf8 strings as name.
        """
        name = purge.name(name)

        # media type is updated if needed
        if self._name != name:
            self.media = guess_type(name)
            self._name = name

    name = property(get_name, set_name)

    def __repr__(self):
        return "<File {0}: {1}@{2}>".format(
            self.id, self.name, self.pluginname)

    @lock
    def init_plugin(self):
        """
        Inits plugin instance.
        """
        if not self.plugin:
            self.pluginclass = self.pyload_core.pgm.get_plugin_class(
                "hoster", self.pluginname)
            self.plugin = self.pluginclass(self)

    @lock(shared=True)
    def has_plugin(self):
        """
        Thread safe way to determine this file has initialized plugin attribute.
        """
        return self.plugin is not None

    def package(self):
        """
        Return package instance.
        """
        return self.__manager.get_package(self.packageid)

    def set_status(self, status):
        self.status = statusmap[status]
        # needs to sync so status is written to database
        self.sync()

    def set_custom_status(self, msg, status="processing"):
        self.statusname = msg
        self.set_status(status)

    def get_status_name(self):
        if self.status not in (15, 16) or not self.statusname:
            return self.__manager.status_msg[self.status]
        else:
            return self.statusname

    def has_status(self, status):
        return statusmap[status] == self.status

    def sync(self):
        """
        Sync File instance with database.
        """
        self.__manager.update_file(self)

    @lock
    def release(self):
        """
        Sync and remove from cache.
        """
        if self.plugin is not None:
            self.plugin.clean()
            self.plugin = None

        self.__manager.release_file(self.fid)

    def to_info_data(self):
        return FileInfo(self.fid, self.get_name(),
                        self.packageid, self.owner, self.size, self.filestatus,
                        self.media, self.added, self.fileorder,
                        DownloadInfo(
                            self.url, self.pluginname, self.hash, self.status,
                            self.get_status_name(),
                            self.error))

    def get_path(self):
        raise NotImplementedError

    def move(self, pid):
        raise NotImplementedError

    # TODO: Recheck
    def abort_download(self):
        """
        Abort file if possible.
        """
        while self.fid in self.pyload_core.tsm.processing_ids():
            with self.lock(shared=True):
                self.abort = True
                if self.plugin and self.plugin.req:
                    self.plugin.req.abort()
                    if self.plugin.dl:
                        self.plugin.dl.abort()
            time.sleep(0.5)

        self.abort = False
        self.set_status("aborted")
        self.release()

    def finish_if_done(self):
        """
        Set status to finish and release file if every thread
        is finished with it.
        """
        # TODO: this is wrong now, it should check if addons are using it
        if self.id in self.pyload_core.tsm.processing_ids():
            return False

        self.set_status("finished")
        self.release()
        self.__manager.check_all_links_finished()
        return True

    def check_if_processed(self):
        self.__manager.check_all_links_processed(self.id)

    @trycatch(0)
    def get_speed(self):
        """
        Calculates speed.
        """
        return self.plugin.dl.speed

    @trycatch(0)
    def get_eta(self):
        """
        Gets estimated time of arrival / or waiting time.
        """
        if self.status == DownloadStatus.Waiting:
            return self.wait_until - time.time()

        return self.get_bytes_left() // self.get_speed()

    @trycatch(0)
    def get_bytes_arrived(self):
        """
        Gets bytes arrived.
        """
        return self.plugin.dl.arrived

    @trycatch(0)
    def get_bytes_left(self):
        """
        Gets bytes left.
        """
        return self.plugin.dl.size - self.plugin.dl.arrived

    @trycatch(0)
    def get_flags(self):
        return self.plugin.dl.flags

    def get_progress_info(self):
        return ProgressInfo(
            self.pluginname, self.name, self.get_status_name(),
            self.get_eta(),
            self.get_bytes_arrived(),
            self.size, self.owner, ProgressType.Download,
            DownloadProgress(
                self.fid, self.packageid, self.get_speed(),
                self.get_flags(),
                self.status))
