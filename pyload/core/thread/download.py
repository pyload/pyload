# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, division, unicode_literals

import sys
import time
from traceback import print_exc

from future import standard_library

from pycurl import error
from pyload.plugins import Abort, Fail, Retry
from pyload.plugins.downloader.hoster.base import Reconnect, Skip
from pyload.plugins.request import ResponseException
from pyload.utils.layer.safethreading import Event
from queue import Queue

from .plugin import PluginThread

standard_library.install_aliases()


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

            except NotImplementedError:
                self.pyload.log.error(
                    _("Plugin {0} is missing a function").format(pyfile.pluginname))
                pyfile.set_status("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.pyload.log.info(
                        _("Download aborted: {0}").format(pyfile.name))
                except Exception:
                    pass

                pyfile.set_status("aborted")

                # abort cleans the file
                # self.clean(pyfile)
                continue

            except Reconnect:
                self.queue.put(pyfile)
                # pyfile.req.clear_cookies()

                while self.manager.reconnecting.isSet():
                    time.sleep(0.5)

                continue

            except Retry as e:
                reason = e.args[0]
                self.pyload.log.info(
                    _("Download restarted: {0} | {1}").format(pyfile.name, reason))
                self.queue.put(pyfile)
                continue
            except Fail as e:
                msg = e.args[0]

                # TODO: activate former skipped downloads

                if msg == "offline":
                    pyfile.set_status("offline")
                    self.pyload.log.warning(
                        _("Download is offline: {0}").format(pyfile.name))
                elif msg == "temp. offline":
                    pyfile.set_status("temp. offline")
                    self.pyload.log.warning(
                        _("Download is temporary offline: {0}").format(pyfile.name))
                else:
                    pyfile.set_status("failed")
                    self.pyload.log.warning(
                        _("Download failed: {0} | {1}").format(pyfile.name, msg))
                    pyfile.error = msg

                self.pyload.adm.download_failed(pyfile)
                self.clean(pyfile)
                continue

            except error as e:
                if len(e.args) == 2:
                    code, msg = e.args
                else:
                    code = 0
                    msg = e.args

                self.pyload.log.debug(
                    "pycurl exception {0}: {1}".format(code, msg))

                if code in (7, 18, 28, 52, 56):
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

                    continue

                else:
                    pyfile.set_status("failed")
                    self.pyload.log.error(
                        _("pycurl error {0}: {1}").format(code, msg))
                    if self.pyload.debug:
                        print_exc()
                        self.write_debug_report(pyfile.plugin.__name__, pyfile)

                    self.pyload.adm.download_failed(pyfile)

                self.clean(pyfile)
                continue

            except Skip as e:
                pyfile.set_status("skipped")

                self.pyload.log.info(
                    _("Download skipped: {0} due to {1}").format(pyfile.name, e.message))

                self.clean(pyfile)

                self.pyload.files.check_package_finished(pyfile)

                self.active = False
                self.pyload.files.save()

                continue

            except Exception as e:
                if isinstance(e, ResponseException) and e.code == 500:
                    pyfile.set_status("temp. offline")
                    self.pyload.log.warning(
                        _("Download is temporary offline: {0}").format(pyfile.name))
                    pyfile.error = _("Internal Server Error")

                else:
                    pyfile.set_status("failed")
                    self.pyload.log.warning(
                        _("Download failed: {0} | {1}").format(pyfile.name, e.message))
                    pyfile.error = e.message

                if self.pyload.debug:
                    print_exc()
                    self.write_debug_report(pyfile.plugin.__name__, pyfile)

                self.pyload.adm.download_failed(pyfile)
                self.clean(pyfile)
                continue

            finally:
                self.pyload.files.save()
                pyfile.check_if_processed()
                sys.exc_clear()
                # manager could still be waiting for it
                self.running.set()

                # only done when job was not put back
                if self.queue.empty():
                    self.manager.done(self)

            # pyfile.plugin.req.clean()

            self.active = False
            pyfile.finish_if_done()
            self.pyload.files.save()

    def get_progress(self):
        if self.active:
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
