# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

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

    def _handle_abort(self, pyfile):
        try:
            self.pyload.log.info(
                _("Download aborted: {0}").format(pyfile.name))
        except Exception:
            pass
        pyfile.set_status("aborted")
        
    def _handle_reconnect(self, pyfile):
        self.queue.put(pyfile)
        # pyfile.req.clear_cookies()
        while self.manager.reconnecting.isSet():
            time.sleep(0.5)
            
    def _handle_retry(self, pyfile, reason):
        self.pyload.log.info(
            _("Download restarted: {0} | {1}").format(pyfile.name, reason))
        self.queue.put(pyfile)
        
    def _handle_notimplement(self, pyfile):
        self.pyload.log.error(
            _("Plugin {0} is missing a function").format(pyfile.pluginname))
        pyfile.set_status("failed")
        pyfile.error = "Plugin does not work"
        self.clean(pyfile)
        
    def _handle_exception(self, pyfile, errmsg, tempoffline=False):
        if tempoffline:
            pyfile.set_status("temp. offline")
            self.pyload.log.warning(
                _("Download is temporary offline: {0}").format(pyfile.name))
            pyfile.error = _("Internal Server Error")
        else:
            pyfile.set_status("failed")
            self.pyload.log.warning(
                _("Download failed: {0} | {1}").format(pyfile.name, errmsg))
            pyfile.error = errmsg

        if self.pyload.debug:
            print_exc()
            self.debug_report(pyfile)

        self.pyload.adm.download_failed(pyfile)
        self.clean(pyfile)
        
    # TODO: activate former skipped downloads
    def _handle_fail(pyfile, errmsg)                    
        if errmsg == "offline":
            pyfile.set_status("offline")
            self.pyload.log.warning(
                _("Download is offline: {0}").format(pyfile.name))
        elif errmsg == "temp. offline":
            pyfile.set_status("temp. offline")
            self.pyload.log.warning(
                _("Download is temporary offline: {0}").format(pyfile.name))
        else:
            pyfile.set_status("failed")
            self.pyload.log.warning(
                _("Download failed: {0} | {1}").format(pyfile.name, errmsg))
            pyfile.error = errmsg

        self.pyload.adm.download_failed(pyfile)
        self.clean(pyfile)
        
    def _handle_skip(self, pyfile, errmsg):
        pyfile.set_status("skipped")

        self.pyload.log.info(
            _("Download skipped: {0} due to {1}").format(pyfile.name, errmsg))

        self.clean(pyfile)

        self.pyload.files.check_package_finished(pyfile)

        self.active = False
        self.pyload.files.save()
        
    def _handle_error(pyfile, errmsg, errcode=None):
        self.pyload.log.debug(
            "pycurl exception {0}: {1}".format(errcode, errmsg))

        if errcode in (7, 18, 28, 52, 56):
            self.pyload.log.warning(
                _("Couldn't connect to host or connection reset, waiting 1 minute and retry"))
            wait = time.time() + 60

            pyfile.wait_until = wait
            pyfile.set_status("waiting")
            while time.time() < wait:
                time.sleep(0.5)

                if pyfile.abort:
                    break

            if pyfile.abort:
                self.pyload.log.info(
                    _("Download aborted: {0}").format(pyfile.name))
                pyfile.set_status("aborted")
                # do not clean, aborting function does this itself
                # self.clean(pyfile)
            else:
                self.queue.put(pyfile)
        else:
            pyfile.set_status("failed")
            self.pyload.log.error(
                _("pycurl error {0}: {1}").format(errcode, errmsg))
            if self.pyload.debug:
                print_exc()
                self.debug_report(pyfile)

            self.pyload.adm.download_failed(pyfile)
        
    def _run(self, pyfile):
        pyfile.init_plugin()

        # after initialization the thread is fully ready
        self.running.set()

        # this pyfile was deleted while queuing
        # TODO: what will happen with new thread manager?
        # if not pyfile.has_plugin(): continue

        pyfile.plugin.check_for_same_files(starting=True)
        self.pyload.log.info(
            _("Download starts: {0}".format(pyfile.name)))

        # start download
        self.pyload.adm.download_preparing(pyfile)
        pyfile.plugin.preprocessing(self)

        self.pyload.log.info(
            _("Download finished: {0}").format(pyfile.name))
        self.pyload.adm.download_finished(pyfile)
        self.pyload.files.check_package_finished(pyfile)
        
    def _finalize(self, pyfile):
        self.pyload.files.save()
        pyfile.check_if_processed()
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
        pyfile = None
        while True:
            del pyfile
            
            self.active = self.queue.get()
            pyfile = self.active

            if self.active == "quit":
                self.active = None
                self.manager.stop(self)
                return True
            try:
                self._run(pyfile)
            except NotImplementedError:
                self._handle_notimplement(pyfile)
                continue
            except Abort:
                self._handle_abort(pyfile)
                # abort cleans the file
                # self.clean(pyfile)
                continue
            except Reconnect:
                self._handle_reconnect(pyfile)
                continue
            except Retry as e:
                self._handle_retry(pyfile, e.args[0])
                continue
            except Fail as e:
                self._handle_fail(pyfile, e.args[0])
                continue
            except error as e:
                errcode = None
                errmsg = e.args
                if len(e.args) == 2:
                    errcode, errmsg = e.args
                self._handle_error(pyfile, errmsg, errcode)
                self.clean(pyfile)
                continue
            except Skip as e:
                self._handle_skip(pyfile, str(e))
                continue
            except Exception as e:
                tempoffline = isinstance(e, ResponseException) and e.code == 500
                self._handle_exception(pyfile, str(e), tempoffline)
                continue
            finally:
                self._finalize(pyfile)
                
            # pyfile.plugin.req.clean()
            self.active = False
            pyfile.finish_if_done()
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

    def clean(self, pyfile):
        """
        Set thread inactive and release pyfile.
        """
        pyfile.release()

    def stop(self):
        """
        Stops the thread.
        """
        self.put("quit")
