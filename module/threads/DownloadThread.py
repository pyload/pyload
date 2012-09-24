#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""

from Queue import Queue
from time import sleep, time
from traceback import print_exc
from sys import exc_clear
from pycurl import error

from module.plugins.Base import Fail, Retry, Abort
from module.plugins.Hoster import Reconnect, SkipDownload
from module.network.HTTPRequest import BadHeader

from BaseThread import BaseThread

class DownloadThread(BaseThread):
    """thread for downloading files from 'real' hoster plugins"""

    def __init__(self, manager):
        """Constructor"""
        BaseThread.__init__(self, manager)

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
                self.m.threads.remove(self)
                return True

            try:
                if not pyfile.hasPlugin(): continue
                #this pyfile was deleted while queuing

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
                except:
                    pass

                pyfile.setStatus("aborted")

                self.clean(pyfile)
                continue

            except Reconnect:
                self.queue.put(pyfile)
                #pyfile.req.clearCookies()

                while self.m.reconnecting.isSet():
                    sleep(0.5)

                continue

            except Retry, e:
                reason = e.args[0]
                self.log.info(_("Download restarted: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": reason})
                self.queue.put(pyfile)
                continue
            except Fail, e:
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

            except error, e:
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
                        sleep(1)
                        if pyfile.abort:
                            break

                    if pyfile.abort:
                        self.log.info(_("Download aborted: %s") % pyfile.name)
                        pyfile.setStatus("aborted")

                        self.clean(pyfile)
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

            except SkipDownload, e:
                pyfile.setStatus("skipped")

                self.log.info(_("Download skipped: %(name)s due to %(plugin)s")
                % {"name": pyfile.name, "plugin": e.message})

                self.clean(pyfile)

                self.core.files.checkPackageFinished(pyfile)

                self.active = False
                self.core.files.save()

                continue


            except Exception, e:
                if isinstance(e, BadHeader) and e.code == 500:
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
        self.active = False
        pyfile.release()

    def stop(self):
        """stops the thread"""
        self.put("quit")
