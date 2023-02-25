# -*- coding: utf-8 -*-

import os
import re
import subprocess
import time
from datetime import timedelta
from random import choice
from threading import Event, Lock

# import pycurl

from ..datatypes.pyfile import PyFile
from ..network.request_factory import get_url
from ..threads.decrypter_thread import DecrypterThread
from ..threads.download_thread import DownloadThread
from ..threads.info_thread import InfoThread
from ..utils import fs
from ..utils.struct.lock import lock


class ThreadManager:
    """
    manages the download threads, assign jobs, reconnect etc.
    """

    def __init__(self, core):
        """
        Constructor.
        """
        self.pyload = core
        self._ = core._

        self.threads = []  #: thread list
        self.local_threads = []  #: addon+decrypter threads

        self.pause = True

        self.reconnecting = Event()
        self.reconnecting.clear()
        self.downloaded = 0  #: number of files downloaded since last cleanup

        self.lock = Lock()

        # some operations require to fetch url info from hoster, so we caching them so it wont be done twice
        # contains a timestamp and will be purged after timeout
        self.info_cache = {}

        # pool of ids for online check
        self.result_ids = 0

        # threads which are fetching hoster results
        self.info_results = {}
        # timeout for cache purge
        self.timestamp = 0

        # pycurl.global_init(pycurl.GLOBAL_DEFAULT)

        for i in range(self.pyload.config.get("download", "max_downloads")):
            self.create_download_thread()

    def create_download_thread(self):
        """
        create a download thread.
        """
        thread = DownloadThread(self)
        self.threads.append(thread)

    def create_info_thread(self, data, pid):
        """
        start a thread whichs fetches online status and other infos
        data = [ .. () .. ]
        """
        self.timestamp = time.time() + timedelta(minutes=5).total_seconds()

        InfoThread(self, data, pid)

    @lock
    def create_result_thread(self, data, add=False):
        """
        creates a thread to fetch online status, returns result id.
        """
        self.timestamp = time.time() + timedelta(minutes=5).total_seconds()

        rid = self.result_ids
        self.result_ids += 1

        InfoThread(self, data, rid=rid, add=add)

        return rid

    @lock
    def get_info_result(self, rid):
        """
        returns result and clears it.
        """
        self.timestamp = time.time() + timedelta(minutes=5).total_seconds()

        if rid in self.info_results:
            data = self.info_results[rid]
            self.info_results[rid] = {}
            return data
        else:
            return {}

    @lock
    def set_info_results(self, rid, result):
        self.info_results[rid].update(result)

    def get_active_files(self):
        active = [
            x.active for x in self.threads if x.active and isinstance(x.active, PyFile)
        ]

        for t in self.local_threads:
            active.extend(t.get_active_files())

        return active

    def processing_ids(self):
        """
        get an id list of all pyfiles processed.
        """
        return [x.id for x in self.get_active_files()]

    def run(self):
        """
        run all task which have to be done (this is for repetivive call by core)
        """
        try:
            self.try_reconnect()
        except Exception as exc:
            self.pyload.log.error(
                self._("Reconnect Failed: {}").format(exc),
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )
            self.reconnecting.clear()
        self.check_thread_count()

        try:
            self.assign_job()
        except Exception:
            self.pyload.log.warning(
                "Assign job error",
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )

            time.sleep(0.5)
            # it may be failed non critical so we try it again
            self.assign_job()

        if (self.info_cache or self.info_results) and self.timestamp < time.time():
            self.info_cache.clear()
            self.info_results.clear()
            self.pyload.log.debug("Cleared Result cache")

    # ----------------------------------------------------------------------
    def try_reconnect(self):
        """
        checks if reconnect needed.
        """
        if not (
            self.pyload.config.get("reconnect", "enabled")
            and self.pyload.api.is_time_reconnect()
        ):
            return False

        active = [
            x.active.plugin.want_reconnect and x.active.plugin.waiting
            for x in self.threads
            if x.active
        ]

        if not (0 < active.count(True) == len(active)):
            return False

        reconnect_script = self.pyload.config.get("reconnect", "script")
        if not os.path.isfile(reconnect_script):
            self.pyload.config.set("reconnect", "enabled", False)
            self.pyload.log.warning(self._("Reconnect script not found!"))
            return

        self.reconnecting.set()

        # Do reconnect
        self.pyload.log.info(self._("Starting reconnect"))

        while [x.active.plugin.waiting for x in self.threads if x.active].count(
            True
        ) != 0:
            time.sleep(0.25)

        old_ip = self.get_ip()

        self.pyload.addon_manager.before_reconnect(old_ip)

        self.pyload.log.debug(f"Old IP: {old_ip}")

        try:
            subprocess.run(reconnect_script)
        except Exception:
            self.pyload.log.warning(self._("Failed executing reconnect script!"))
            self.pyload.config.set("reconnect", "enabled", False)
            self.reconnecting.clear()
            return

        time.sleep(1)
        ip = self.get_ip()
        self.pyload.addon_manager.after_reconnect(ip, old_ip)

        self.pyload.log.info(self._("Reconnected, new IP: {}").format(ip))

        self.reconnecting.clear()

    def get_ip(self):
        """
        retrieve current ip.
        """
        services = [
            ("https://icanhazip.com/", r"(\S+)"),
            ("http://checkip.dyndns.org/", r".*Current IP Address: (\S+)</body>.*"),
            ("https://ifconfig.io/ip", r"(\S+)"),
        ]

        ip = ""
        for i in range(10):
            try:
                sv = choice(services)
                ip = get_url(sv[0])
                ip = re.match(sv[1], ip).group(1)
                break
            except Exception:
                ip = ""
                time.sleep(1)

        return ip

    # ----------------------------------------------------------------------
    def check_thread_count(self):
        """
        checks if there are need for increasing or reducing thread count.
        """
        if len(self.threads) == self.pyload.config.get("download", "max_downloads"):
            return True
        elif len(self.threads) < self.pyload.config.get("download", "max_downloads"):
            self.create_download_thread()
        else:
            free = [x for x in self.threads if not x.active]
            if free:
                free[0].put("quit")

    # def clean_pycurl(self):
    # """
    # make a global curl cleanup (currently ununused)
    # """
    # if self.processing_ids():
    # return False
    # pycurl.global_cleanup()
    # pycurl.global_init(pycurl.GLOBAL_DEFAULT)
    # self.downloaded = 0
    # self.pyload.log.debug("Cleaned up pycurl")
    # return True

    # ----------------------------------------------------------------------
    def assign_job(self):
        """
        assign a job to a thread if possible.
        """
        if self.pause or not self.pyload.api.is_time_download():
            return

        # if self.downloaded > 20:
        #    if not self.clean_pycurl(): return

        free_threads = [x for x in self.threads if not x.active]

        inuse_plugins = set(
            [
                (x.active.pluginname, self.get_limit(x))
                for x in self.threads
                if x.active and x.active.has_plugin()
            ]
        )
        # (pluginname, dl_limit, active_count)
        inuse_plugins = [
            (
                x[0],
                x[1],
                len(
                    [
                        y
                        for y in self.threads
                        if y.active and y.active.pluginname == x[0]
                    ]
                ),
            )
            for x in inuse_plugins
        ]

        over_limit_plugins = [x[0] for x in inuse_plugins if x[2] >= x[1] > 0]

        occupied_plugins = sorted(
            [
                x.active.pluginname
                for x in self.threads
                if x.active and x.active.has_plugin() and not x.active.plugin.multi_dl
            ]
            + over_limit_plugins
        )

        occupied_plugins = tuple(set(occupied_plugins))  # remove duplicates
        job = self.pyload.files.get_job(occupied_plugins)
        if job:
            try:
                job.init_plugin()
            except Exception as exc:
                self.pyload.log.critical(
                    exc, exc_info=True, stack_info=self.pyload.debug > 2
                )
                job.set_status("failed")
                job.error = str(exc)
                job.release()
                return

            if job.plugin.__type__ == "downloader":
                space_left = (
                    fs.free_space(self.pyload.config.get("general", "storage_folder"))
                    >> 20
                )
                if space_left < self.pyload.config.get("general", "min_free_space"):
                    self.pyload.log.warning(self._("Not enough space left on device"))
                    self.pause = True

                if free_threads and not self.pause:
                    thread = free_threads[0]
                    # self.downloaded += 1

                    job.set_status("starting")
                    thread.put(job)
                else:
                    # put job back
                    if occupied_plugins not in self.pyload.files.job_cache:
                        self.pyload.files.job_cache[occupied_plugins] = []
                    self.pyload.files.job_cache[occupied_plugins].append(job.id)

                    # check for decrypt jobs
                    job = self.pyload.files.get_decrypt_job()
                    if job:
                        job.init_plugin()
                        thread = DecrypterThread(self, job)

            else:
                thread = DecrypterThread(self, job)

    def get_limit(self, thread):
        if thread.active.plugin.account:
            account_limit = max(
                int(
                    thread.active.plugin.account.get_account_data(
                        thread.active.plugin.account.user
                    )["options"].get("limit_dl", ["0"])[0]
                ),
                0,
            )
        else:
            account_limit = 0

        plugin_limit = (
            max(thread.active.plugin.limit_dl, 0)
            if hasattr(thread.active.plugin, "limit_dl")
            else 0
        )
        if account_limit > 0 and plugin_limit > 0:
            limit = min(account_limit, plugin_limit)
        else:
            limit = account_limit or plugin_limit

        return limit

    # def cleanup(self):
    # """
    # do global cleanup, should be called when finished with pycurl.
    # """
    # pycurl.global_cleanup()
