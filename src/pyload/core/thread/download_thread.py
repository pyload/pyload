# -*- coding: utf-8 -*-
# AUTHOR: RaNaN, vuolter

import time
from builtins import str
from queue import Queue

import pycurl
from pyload.plugins.plugin import Abort, Fail, Reconnect, Retry, SkipDownload

from .plugin_thread import PluginThread


class DownloadThread(PluginThread):
    """
    thread for downloading files from 'real' hoster plugins.
    """

    # ----------------------------------------------------------------------
    def __init__(self, manager):
        """
        Constructor.
        """
        super().__init__(manager)

        self.queue = Queue()  #: job queue
        self.active = False

        self.start()

    # ----------------------------------------------------------------------
    def run(self):
        """
        run method.
        """
        pyfile = None

        while True:
            del pyfile
            self.active = self.queue.get()
            pyfile = self.active

            if self.active == "quit":
                self.active = False
                self.m.threads.remove(self)
                return True

            try:
                if not pyfile.hasPlugin():
                    continue
                # this pyfile was deleted while queueing

                pyfile.plugin.checkForSameFiles(starting=True)
                self.m.log.info(self._("Download starts: {}".format(pyfile.name)))

                # start download
                self.m.pyload.addonManager.downloadPreparing(pyfile)
                pyfile.plugin.preprocessing(self)

                self.m.log.info(self._("Download finished: {}").format(pyfile.name))
                self.m.pyload.addonManager.downloadFinished(pyfile)
                self.m.pyload.files.checkPackageFinished(pyfile)

            except NotImplementedError:
                self.m.log.error(
                    self._("Plugin {} is missing a function.").format(pyfile.pluginname)
                )
                pyfile.setStatus("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.m.log.info(self._("Download aborted: {}").format(pyfile.name))
                except Exception:
                    pass

                pyfile.setStatus("aborted")

                self.clean(pyfile)
                continue

            except Reconnect:
                self.queue.put(pyfile)
                # pyfile.req.clearCookies()

                while self.m.reconnecting.isSet():
                    time.sleep(0.5)

                continue

            except Retry as exc:
                reason = exc.args[0]
                self.m.log.info(
                    self._("Download restarted: {name} | {msg}").format(
                        name=pyfile.name, msg=reason
                    )
                )
                self.queue.put(pyfile)
                continue

            except Fail as exc:
                msg = exc.args[0]

                if msg == "offline":
                    pyfile.setStatus("offline")
                    self.m.log.warning(
                        self._("Download is offline: {}").format(pyfile.name)
                    )
                elif msg == "temp. offline":
                    pyfile.setStatus("temp. offline")
                    self.m.log.warning(
                        self._("Download is temporary offline: {}").format(pyfile.name)
                    )
                else:
                    pyfile.setStatus("failed")
                    self.m.log.warning(
                        self._("Download failed: {name} | {msg}").format(
                            name=pyfile.name, msg=msg
                        )
                    )
                    pyfile.error = msg

                self.m.pyload.addonManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            except pycurl.error as exc:
                if len(exc.args) == 2:
                    code, msg = exc.args
                else:
                    code = 0
                    msg = exc.args

                self.m.log.debug("pycurl exception {}: {}".format(code, msg))

                if code in (7, 18, 28, 52, 56):
                    self.m.log.warning(
                        self._(
                            "Couldn't connect to host or connection reset, waiting 1 minute and retry."
                        )
                    )
                    wait = time.time() + 60

                    pyfile.waitUntil = wait
                    pyfile.setStatus("waiting")
                    while time.time() < wait:
                        time.sleep(1)
                        if pyfile.abort:
                            break

                    if pyfile.abort:
                        self.m.log.info(
                            self._("Download aborted: {}").format(pyfile.name)
                        )
                        pyfile.setStatus("aborted")

                        self.clean(pyfile)
                    else:
                        self.queue.put(pyfile)

                    continue

                else:
                    pyfile.setStatus("failed")
                    self.m.log.error("pycurl error {}: {}".format(code, msg))
                    if self.m.pyload.debug:
                        self.writeDebugReport(pyfile)

                    self.m.pyload.addonManager.downloadFailed(pyfile)

                self.clean(pyfile)
                continue

            except SkipDownload as exc:
                pyfile.setStatus("skipped")

                self.m.log.info(
                    self._("Download skipped: {name} due to {plugin}").format(
                        name=pyfile.name, plugin=exc
                    )
                )

                self.clean(pyfile)

                self.m.pyload.files.checkPackageFinished(pyfile)

                self.active = False
                self.m.pyload.files.save()

                continue

            except Exception as exc:
                pyfile.setStatus("failed")
                self.m.log.warning(
                    self._("Download failed: {name} | {msg}").format(
                        name=pyfile.name, msg=exc
                    )
                )
                pyfile.error = str(exc)

                if self.m.pyload.debug:
                    self.writeDebugReport(pyfile)

                self.m.pyload.addonManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            finally:
                self.m.pyload.files.save()
                pyfile.checkIfProcessed()
                # exc_clear()

            # pyfile.plugin.req.clean()

            self.active = False
            pyfile.finishIfDone()
            self.m.pyload.files.save()

    def put(self, job):
        """
        assing job to thread.
        """
        self.queue.put(job)

    def stop(self):
        """
        stops the thread.
        """
        self.put("quit")
