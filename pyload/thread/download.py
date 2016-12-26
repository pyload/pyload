# -*- coding: utf-8 -*-
#@author: RaNaN

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

from pyload.plugin import Fail, Retry, Abort
from pyload.plugin.hoster import Reconnect, SkipDownload
from pyload.plugin.request import ResponseException

from pyload.thread.base import BaseThread


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
                self.manager.stop(self)
                return True

            try:
                pyfile.initPlugin()

                # after initialization the thread is fully ready
                self.isWorking.set()

                #this pyfile was deleted while queuing
                # TODO: what will happen with new thread manager?
                #if not pyfile.has_plugin(): continue


                pyfile.plugin.check_for_same_files(starting=True)
                self.log.info(_("Download starts: %s" % pyfile.name))

                # start download
                self.pyload.addonmanager.download_preparing(pyfile)
                pyfile.plugin.preprocessing(self)

                self.log.info(_("Download finished: %s") % pyfile.name)
                self.pyload.addonmanager.download_finished(pyfile)
                self.pyload.files.check_package_finished(pyfile)

            except NotImplementedError:
                self.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
                pyfile.set_status("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.log.info(_("Download aborted: %s") % pyfile.name)
                except Exception:
                    pass

                pyfile.set_status("aborted")

                # abort cleans the file
                # self.clean(pyfile)
                continue

            except Reconnect:
                self.queue.put(pyfile)
                #pyfile.req.clearCookies()

                while self.manager.reconnecting.isSet():
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
                    pyfile.set_status("offline")
                    self.log.warning(_("Download is offline: %s") % pyfile.name)
                elif msg == "temp. offline":
                    pyfile.set_status("temp. offline")
                    self.log.warning(_("Download is temporary offline: %s") % pyfile.name)
                else:
                    pyfile.set_status("failed")
                    self.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                    pyfile.error = msg

                self.pyload.addonmanager.download_failed(pyfile)
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
                    pyfile.set_status("waiting")
                    while time() < wait:
                        sleep(0.5)

                        if pyfile.abort:
                            break

                    if pyfile.abort:
                        self.log.info(_("Download aborted: %s") % pyfile.name)
                        pyfile.set_status("aborted")
                        # don't clean, aborting function does this itself
                        # self.clean(pyfile)
                    else:
                        self.queue.put(pyfile)

                    continue

                else:
                    pyfile.set_status("failed")
                    self.log.error("pycurl error %s: %s" % (code, msg))
                    if self.pyload.debug:
                        print_exc()
                        self.write_debug_report(pyfile.plugin.__name__, pyfile)

                    self.pyload.addonmanager.download_failed(pyfile)

                self.clean(pyfile)
                continue

            except SkipDownload as e:
                pyfile.set_status("skipped")

                self.log.info(_("Download skipped: %(name)s due to %(plugin)s")
                % {"name": pyfile.name, "plugin": e.message})

                self.clean(pyfile)

                self.pyload.files.check_package_finished(pyfile)

                self.active = False
                self.pyload.files.save()

                continue

            except Exception as e:
                if isinstance(e, ResponseException) and e.code == 500:
                    pyfile.set_status("temp. offline")
                    self.log.warning(_("Download is temporary offline: %s") % pyfile.name)
                    pyfile.error = _("Internal Server Error")

                else:
                    pyfile.set_status("failed")
                    self.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": str(e)})
                    pyfile.error = str(e)

                if self.pyload.debug:
                    print_exc()
                    self.write_debug_report(pyfile.plugin.__name__, pyfile)

                self.pyload.addonmanager.download_failed(pyfile)
                self.clean(pyfile)
                continue

            finally:
                self.pyload.files.save()
                pyfile.checkIfProcessed()
                exc_clear()
                # manager could still be waiting for it
                self.isWorking.set()

                # only done when job was not put back
                if self.queue.empty():
                    self.manager.done(self)

            #pyfile.plugin.req.clean()

            self.active = False
            pyfile.finishIfDone()
            self.pyload.files.save()

    def get_progress(self):
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
