# -*- coding: utf-8 -*-

import time
from threading import RLock

from ..managers.event_manager import UpdateEvent
from ..utils import format
from ..utils.old import lock

status_map = {
    "finished": 0,
    "offline": 1,
    "online": 2,
    "queued": 3,
    "skipped": 4,
    "waiting": 5,
    "temp. offline": 6,
    "starting": 7,
    "failed": 8,
    "aborted": 9,
    "decrypting": 10,
    "custom": 11,
    "downloading": 12,
    "processing": 13,
    "unknown": 14,
}


def set_size(self, value):
    self._size = int(value)


class PyFile:
    """
    Represents a file object at runtime.
    """

    def __init__(
        self, manager, id, url, name, size, status, error, pluginname, package, order
    ):
        self.m = self.manager = manager
        self.m.cache[int(id)] = self

        self.id = int(id)
        self.url = url
        self.name = name

        self._size = None
        self.size = size

        self.status = status
        self.pluginname = pluginname
        self.packageid = package  #: should not be used, use package() instead
        self.error = error
        self.order = order
        # database information ends here

        self.lock = RLock()

        self.plugin = None
        # self.download = None

        self.wait_until = 0  #: time.time() + time to wait

        # status attributes
        self.active = False  #: obsolete?
        self.abort = False
        self.reconnected = False

        self.statusname = None

        self.progress = 0
        self.maxprogress = 100

    # will convert all sizes to ints
    size = property(lambda self: self._size, set_size)

    def __repr__(self):
        return f"PyFile {self.id}: {self.name}@{self.pluginname}"

    @lock
    def init_plugin(self):
        """
        inits plugin instance.
        """
        if not self.plugin:
            self.pluginmodule = self.m.pyload.plugin_manager.get_plugin(self.pluginname)
            self.pluginclass = getattr(
                self.pluginmodule,
                self.m.pyload.plugin_manager.get_plugin_name(self.pluginname),
            )
            self.plugin = self.pluginclass(self)

    @lock
    def has_plugin(self):
        """
        Thread safe way to determine this file has initialized plugin attribute.

        :return:
        """
        return hasattr(self, "plugin") and self.plugin

    def package(self):
        """
        return package instance.
        """
        return self.m.get_package(self.packageid)

    def set_status(self, status):
        self.status = status_map[status]
        self.sync()  # TODO: needed aslong no better job approving exists

    def set_custom_status(self, msg, status="processing"):
        self.statusname = msg
        self.set_status(status)

    def get_status_name(self):
        if self.status not in (13, 14) or not self.statusname:
            return self.m.status_msg[self.status]
        else:
            return self.statusname

    def has_status(self, status):
        return status_map[status] == self.status

    def sync(self):
        """
        sync PyFile instance with database.
        """
        self.m.update_link(self)

    @lock
    def release(self):
        """
        sync and remove from cache.
        """
        # file has valid package
        if self.packageid > 0:
            self.sync()

        if hasattr(self, "plugin") and self.plugin:
            self.plugin.clean()
            del self.plugin

        self.m.release_link(self.id)

    def delete(self):
        """
        delete pyfile from database.
        """
        self.m.delete_link(self.id)

    def to_dict(self):
        """
        return dict with all information for interface.
        """
        return self.to_db_dict()

    def to_db_dict(self):
        """
        return data as dict for databse.

        format:

        {
            id: {'url': url, 'name': name ... }
        }
        """
        return {
            self.id: {
                "id": self.id,
                "url": self.url,
                "name": self.name,
                "plugin": self.pluginname,
                "size": self.get_size(),
                "format_size": self.format_size(),
                "status": self.status,
                "statusmsg": self.get_status_name(),
                "package": self.packageid,
                "error": self.error,
                "order": self.order,
            }
        }

    def abort_download(self):
        """
        abort pyfile if possible.
        """
        while self.id in self.m.pyload.thread_manager.processing_ids():
            self.abort = True
            if self.plugin and self.plugin.req:
                self.plugin.req.abort_downloads()
            time.sleep(0.1)

        self.abort = False
        if self.has_plugin() and self.plugin.req:
            self.plugin.req.abort_downloads()

        self.release()

    def finish_if_done(self):
        """
        set status to finish and release file if every thread is finished with it.
        """
        if self.id in self.m.pyload.thread_manager.processing_ids():
            return False

        self.set_status("finished")
        self.release()
        self.m.check_all_links_finished()
        return True

    def check_if_processed(self):
        self.m.check_all_links_processed(self.id)

    def format_wait(self):
        """
        formats and return wait time in humanreadable format.
        """
        seconds = self.wait_until - time.time()

        if seconds < 0:
            return "00:00:00"

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def format_size(self):
        """
        formats size to readable format.
        """
        return format.size(self.get_size())

    def format_eta(self):
        """
        formats eta to readable format.
        """
        seconds = self.get_eta()

        if seconds < 0:
            return "00:00:00"

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

    def get_speed(self):
        """
        calculates speed.
        """
        try:
            return self.plugin.req.speed
        except Exception:
            return 0

    def get_eta(self):
        """
        gets established time of arrival.
        """
        try:
            return self.get_bytes_left() // self.get_speed()
        except Exception:
            return 0

    def get_bytes_left(self):
        """
        gets bytes left.
        """
        try:
            return self.plugin.req.size - self.plugin.req.arrived
        except Exception:
            return 0

    def get_percent(self):
        """
        get % of download.
        """
        if self.status == 12:
            try:
                return self.plugin.req.percent
            except Exception:
                return 0
        else:
            return self.progress

    def get_size(self):
        """
        get size of download.
        """
        try:
            if self.plugin.req.size:
                return self.plugin.req.size
            else:
                return self.size
        except Exception:
            return self.size

    def notify_change(self):
        e = UpdateEvent(
            "file", self.id, "collector" if not self.package().queue else "queue"
        )
        self.m.pyload.event_manager.add_event(e)

    def set_progress(self, value):
        if not value == self.progress:
            self.progress = value
            self.notify_change()
