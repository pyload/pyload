# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from builtins import str
import sys
import time
from traceback import print_exc

from future import standard_library
standard_library.install_aliases()

from pycurl import error
from pyload.plugins import Abort, Fail, Retry
from pyload.plugins.downloader.hoster.base import Reconnect, Skip
from pyload.plugins.request import ResponseException
from pyload.utils.layer.safethreading import Event
from queue import Queue

from .plugin import PluginThread


class DownloadThread(PluginThread):
    """
    Thread for downloading files from 'real' hoster plugins.
    """
    __slots__ = ['active', 'queue', 'running']

    def __init__(self, manager):
        """
        Constructor.
        """
        PluginThread.__init__(self, manager)

        self.running = Event()
        self.queue = Queue()  #: job queue
        self.active = None

        self.start()

    def _handle_abort(self, file):
        try:
            self.pyload.log.info(
                _("Download aborted: {0}").format(file.name))
        except Exception:
            pass
        file.set_status("aborted")

    def _handle_reconnect(self, file):
        self.queue.put(file)
        # file.req.clear_cookies()
        while self.manager.reconnecting.isSet():
            time.sleep(0.5)

    def _handle_retry(self, file, reason):
        self.pyload.log.info(
            _("Download restarted: {0} | {1}").format(file.name, reason))
        self.queue.put(file)

    def _handle_notimplement(self, file):
        self.pyload.log.error(
            _("Plugin {0} is missing a function").format(file.pluginname))
        file.set_status("failed")
        file.error = "Plugin does not work"
        self.clean(file)

    def _handle_exception(self, file, errmsg, tempoffline=False):
        if tempoffline:
            file.set_status("temp. offline")
            self.pyload.log.warning(
                _("Download is temporary offline: {0}").format(file.name))
            file.error = _("Internal Server Error")
        else:
            file.set_status("failed")
            self.pyload.log.warning(
                _("Download failed: {0} | {1}").format(file.name, errmsg))
            file.error = errmsg

        if self.pyload.debug:
            print_exc()
            self.debug_report(file)

        self.pyload.adm.download_failed(file)
        self.clean(file)

    # TODO: activate former skipped downloads
    def _handle_fail(file, errmsg):
        if errmsg == "offline":
            file.set_status("offline")
            self.pyload.log.warning(
                _("Download is offline: {0}").format(file.name))
        elif errmsg == "temp. offline":
            file.set_status("temp. offline")
            self.pyload.log.warning(
                _("Download is temporary offline: {0}").format(file.name))
        else:
            file.set_status("failed")
            self.pyload.log.warning(
                _("Download failed: {0} | {1}").format(file.name, errmsg))
            file.error = errmsg

        self.pyload.adm.download_failed(file)
        self.clean(file)

    def _handle_skip(self, file, errmsg):
        file.set_status("skipped")

        self.pyload.log.info(
            _("Download skipped: {0} due to {1}").format(file.name, errmsg))

        self.clean(file)

        self.pyload.files.check_package_finished(file)

        self.active = False
        self.pyload.files.save()

    def _handle_error(file, errmsg, errcode=None):
        self.pyload.log.debug(
            "pycurl exception {0}: {1}".format(errcode, errmsg))

        if errcode in (7, 18, 28, 52, 56):
            self.pyload.log.warning(
                _("Couldn't connect to host or connection reset, waiting 1 minute and retry"))
            wait = time.time() + 60

            file.wait_until = wait
            file.set_status("waiting")
            while time.time() < wait:
                time.sleep(0.5)

                if file.abort:
                    break

            if file.abort:
                self.pyload.log.info(
                    _("Download aborted: {0}").format(file.name))
                file.set_status("aborted")
                # do not clean, aborting function does this itself
                # self.clean(file)
            else:
                self.queue.put(file)
        else:
            file.set_status("failed")
            self.pyload.log.error(
                _("pycurl error {0}: {1}").format(errcode, errmsg))
            if self.pyload.debug:
                print_exc()
                self.debug_report(file)

            self.pyload.adm.download_failed(file)

    def _run(self, file):
        file.init_plugin()

        # after initialization the thread is fully ready
        self.running.set()

        # this file was deleted while queuing
        # TODO: what will happen with new thread manager?
        # if not file.has_plugin(): continue

        file.plugin.check_for_same_files(starting=True)
        self.pyload.log.info(
            _("Download starts: {0}".format(file.name)))

        # start download
        self.pyload.adm.download_preparing(file)
        file.plugin.preprocessing(self)

        self.pyload.log.info(
            _("Download finished: {0}").format(file.name))
        self.pyload.adm.download_finished(file)
        self.pyload.files.check_package_finished(file)

    def _finalize(self, file):
        self.pyload.files.save()
        file.check_if_processed()
        sys.exc_clear()
        # manager could still be waiting for it
        self.running.set()
        # only done when job was not put back
        if self.queue.empty():
            self.manager.done(self)

    def run(self):
        """
        Run method.
        """
        file = None
        while True:
            del file

            self.active = self.queue.get()
            file = self.active

            if self.active == "quit":
                self.active = None
                self.manager.stop(self)
                return True
            try:
                self._run(file)
            except NotImplementedError:
                self._handle_notimplement(file)
                continue
            except Abort:
                self._handle_abort(file)
                # abort cleans the file
                # self.clean(file)
                continue
            except Reconnect:
                self._handle_reconnect(file)
                continue
            except Retry as e:
                self._handle_retry(file, e.args[0])
                continue
            except Fail as e:
                self._handle_fail(file, e.args[0])
                continue
            except error as e:
                errcode = None
                errmsg = e.args
                if len(e.args) == 2:
                    errcode, errmsg = e.args
                self._handle_error(file, errmsg, errcode)
                self.clean(file)
                continue
            except Skip as e:
                self._handle_skip(file, str(e))
                continue
            except Exception as e:
                tempoffline = isinstance(e, ResponseException) and e.code == 500
                self._handle_exception(file, str(e), tempoffline)
                continue
            finally:
                self._finalize(file)

            # file.plugin.req.clean()
            self.active = False
            file.finish_if_done()
            self.pyload.files.save()

    def get_progress(self):
        if not self.active:
            return None
        return self.active.get_progress_info()

    def put(self, job):
        """
        Assign a job to the thread.
        """
        self.queue.put(job)

    def clean(self, file):
        """
        Set thread inactive and release file.
        """
        file.release()

    def stop(self):
        """
        Stops the thread.
        """
        self.put("quit")
