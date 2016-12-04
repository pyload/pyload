# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
#   https://pyload.net
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from threading import Event
from queue import Queue
from time import sleep, time
from traceback import print_exc
from sys import exc_clear
from pycurl import error

from pyload.plugins.Base import Fail, Retry, Abort
from pyload.plugins.Hoster import Reconnect, SkipDownload
from pyload.plugins.Request import ResponseException

from .BaseThread import BaseThread


class DownloadThread(BaseThread):
    """thread for downloading files from 'real' hoster plugins"""

    def __init__(self, manager):
        """Constructor"""
        BaseThread.__init__(self, manager)

        self.isWorking = Event()
        self.isWorking.clear()

        self.queue = Queue() # job queue
        self.active = None

        self.start()

    def run(self):
        """run method"""
        pyfile = None

        while True:
            del pyfile
            self.active = self.queue.get()
            pyfile = self.active

            if self.active == "quit":
                self.active = None
                self.m.stop(self)
                return True

            try:
                pyfile.initPlugin()

                # after initialization the thread is fully ready
                self.isWorking.set()

                #this pyfile was deleted while queuing
                # TODO: what will happen with new thread manager?
                #if not pyfile.hasPlugin(): continue


                pyfile.plugin.checkForSameFiles(starting=True)
                self.log.info(_("Download starts: %s" % pyfile.name))

                # start download
                self.core.addonManager.downloadPreparing(pyfile)
                pyfile.plugin.preprocessing(self)

                self.log.info(_("Download finished: %s") % pyfile.name)
                self.core.addonManager.downloadFinished(pyfile)
                self.core.files.checkPackageFinished(pyfile)

            except NotImplementedError:
                self.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
                pyfile.setStatus("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.log.info(_("Download aborted: %s") % pyfile.name)
                except Exception:
                    pass

                pyfile.setStatus("aborted")

                # abort cleans the file
                # self.clean(pyfile)
                continue

            except Reconnect:
                self.queue.put(pyfile)
                #pyfile.req.clearCookies()

                while self.m.reconnecting.isSet():
                    sleep(0.5)

                continue

            except Retry as e:
                reason = e.args[0]
                self.log.info(_("Download restarted: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": reason})
                self.queue.put(pyfile)
                continue
            except Fail as e:
                msg = e.args[0]

                # TODO: activate former skipped downloads

                if msg == "offline":
                    pyfile.setStatus("offline")
                    self.log.warning(_("Download is offline: %s") % pyfile.name)
                elif msg == "temp. offline":
                    pyfile.setStatus("temp. offline")
                    self.log.warning(_("Download is temporary offline: %s") % pyfile.name)
                else:
                    pyfile.setStatus("failed")
                    self.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                    pyfile.error = msg

                self.core.addonManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            except error as e:
                if len(e.args) == 2:
                    code, msg = e.args
                else:
                    code = 0
                    msg = e.args

                self.log.debug("pycurl exception %s: %s" % (code, msg))

                if code in (7, 18, 28, 52, 56):
                    self.log.warning(_("Couldn't connect to host or connection reset, waiting 1 minute and retry."))
                    wait = time() + 60

                    pyfile.waitUntil = wait
                    pyfile.setStatus("waiting")
                    while time() < wait:
                        sleep(0.5)

                        if pyfile.abort:
                            break

                    if pyfile.abort:
                        self.log.info(_("Download aborted: %s") % pyfile.name)
                        pyfile.setStatus("aborted")
                        # don't clean, aborting function does this itself
                        # self.clean(pyfile)
                    else:
                        self.queue.put(pyfile)

                    continue

                else:
                    pyfile.setStatus("failed")
                    self.log.error("pycurl error %s: %s" % (code, msg))
                    if self.core.debug:
                        print_exc()
                        self.writeDebugReport(pyfile.plugin.__name__, pyfile)

                    self.core.addonManager.downloadFailed(pyfile)

                self.clean(pyfile)
                continue

            except SkipDownload as e:
                pyfile.setStatus("skipped")

                self.log.info(_("Download skipped: %(name)s due to %(plugin)s")
                % {"name": pyfile.name, "plugin": e.message})

                self.clean(pyfile)

                self.core.files.checkPackageFinished(pyfile)

                self.active = False
                self.core.files.save()

                continue

            except Exception as e:
                if isinstance(e, ResponseException) and e.code == 500:
                    pyfile.setStatus("temp. offline")
                    self.log.warning(_("Download is temporary offline: %s") % pyfile.name)
                    pyfile.error = _("Internal Server Error")

                else:
                    pyfile.setStatus("failed")
                    self.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": str(e)})
                    pyfile.error = str(e)

                if self.core.debug:
                    print_exc()
                    self.writeDebugReport(pyfile.plugin.__name__, pyfile)

                self.core.addonManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            finally:
                self.core.files.save()
                pyfile.checkIfProcessed()
                exc_clear()
                # manager could still be waiting for it
                self.isWorking.set()

                # only done when job was not put back
                if self.queue.empty():
                    self.m.done(self)

            #pyfile.plugin.req.clean()

            self.active = False
            pyfile.finishIfDone()
            self.core.files.save()

    def getProgress(self):
        if self.active:
            return self.active.getProgressInfo()

    def put(self, job):
        """assign a job to the thread"""
        self.queue.put(job)

    def clean(self, pyfile):
        """ set thread inactive and release pyfile """
        pyfile.release()

    def stop(self):
        """stops the thread"""
        self.put("quit")
