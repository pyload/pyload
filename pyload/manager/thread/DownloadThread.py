# -*- coding: utf-8 -*-
# @author: RaNaN

from Queue import Queue
from threading import Thread
from os import listdir, stat
from os.path import join
from time import sleep, time, strftime, gmtime
from traceback import print_exc, format_exc
from pprint import pformat
from sys import exc_info, exc_clear
from copy import copy
from types import MethodType

from pycurl import error

from pyload.datatype.PyFile import PyFile
from pyload.manager.thread.PluginThread import PluginThread
from pyload.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload
from pyload.utils.packagetools import parseNames
from pyload.utils import safe_join
from pyload.api import OnlineStatus


class DownloadThread(PluginThread):
    """thread for downloading files from 'real' hoster plugins"""

    #--------------------------------------------------------------------------
    def __init__(self, manager):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.queue = Queue()  #: job queue
        self.active = False

        self.start()

    #--------------------------------------------------------------------------
    def run(self):
        """run method"""
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
                #this pyfile was deleted while queueing

                pyfile.plugin.checkForSameFiles(starting=True)
                self.m.log.info(_("Download starts: %s" % pyfile.name))

                # start download
                self.m.core.addonManager.downloadPreparing(pyfile)
                pyfile.error = ""
                pyfile.plugin.preprocessing(self)

                self.m.log.info(_("Download finished: %s") % pyfile.name)
                self.m.core.addonManager.downloadFinished(pyfile)
                self.m.core.files.checkPackageFinished(pyfile)

            except NotImplementedError:
                self.m.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
                pyfile.setStatus("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.m.log.info(_("Download aborted: %s") % pyfile.name)
                except Exception:
                    pass

                pyfile.setStatus("aborted")

                if self.m.core.debug:
                    print_exc()

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
                self.m.log.info(_("Download restarted: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": reason})
                self.queue.put(pyfile)
                continue

            except Fail, e:
                msg = e.args[0]

                if msg == "offline":
                    pyfile.setStatus("offline")
                    self.m.log.warning(_("Download is offline: %s") % pyfile.name)
                elif msg == "temp. offline":
                    pyfile.setStatus("temp. offline")
                    self.m.log.warning(_("Download is temporary offline: %s") % pyfile.name)
                else:
                    pyfile.setStatus("failed")
                    self.m.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                    pyfile.error = msg

                if self.m.core.debug:
                    print_exc()

                self.m.core.addonManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            except error, e:
                if len(e.args) == 2:
                    code, msg = e.args
                else:
                    code = 0
                    msg = e.args

                self.m.log.debug("pycurl exception %s: %s" % (code, msg))

                if code in (7, 18, 28, 52, 56):
                    self.m.log.warning(_("Couldn't connect to host or connection reset, waiting 1 minute and retry."))
                    wait = time() + 60

                    pyfile.waitUntil = wait
                    pyfile.setStatus("waiting")
                    while time() < wait:
                        sleep(1)
                        if pyfile.abort:
                            break

                    if pyfile.abort:
                        self.m.log.info(_("Download aborted: %s") % pyfile.name)
                        pyfile.setStatus("aborted")

                        self.clean(pyfile)
                    else:
                        self.queue.put(pyfile)

                    continue

                else:
                    pyfile.setStatus("failed")
                    self.m.log.error("pycurl error %s: %s" % (code, msg))
                    if self.m.core.debug:
                        print_exc()
                        self.writeDebugReport(pyfile)

                    self.m.core.addonManager.downloadFailed(pyfile)

                self.clean(pyfile)
                continue

            except SkipDownload, e:
                pyfile.setStatus("skipped")

                self.m.log.info(
                    _("Download skipped: %(name)s due to %(plugin)s") % {"name": pyfile.name, "plugin": e.message})

                self.clean(pyfile)

                self.m.core.files.checkPackageFinished(pyfile)

                self.active = False
                self.m.core.files.save()

                continue


            except Exception, e:
                pyfile.setStatus("failed")
                self.m.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": str(e)})
                pyfile.error = str(e)

                if self.m.core.debug:
                    print_exc()
                    self.writeDebugReport(pyfile)

                self.m.core.addonManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            finally:
                self.m.core.files.save()
                pyfile.checkIfProcessed()
                exc_clear()

            #pyfile.plugin.req.clean()

            self.active = False
            pyfile.finishIfDone()
            self.m.core.files.save()


    def put(self, job):
        """assing job to thread"""
        self.queue.put(job)


    def stop(self):
        """stops the thread"""
        self.put("quit")
