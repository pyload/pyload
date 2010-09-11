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
from threading import Thread
from time import sleep
from time import strftime
from traceback import print_exc, format_exc
from pprint import pformat
from sys import exc_info
from types import MethodType
from os.path import join, exists

from module.plugins.Plugin import Abort
from module.plugins.Plugin import Fail
from module.plugins.Plugin import Reconnect
from module.plugins.Plugin import Retry
from pycurl import error
from module.FileDatabase import PyFile

########################################################################
class PluginThread(Thread):
    """abstract base class for thread types"""

    #----------------------------------------------------------------------
    def __init__(self, manager):
        """Constructor"""
        Thread.__init__(self)
        self.setDaemon(True)
        self.m = manager #thread manager


    def writeDebugReport(self, pyfile):
        dump = "pyLoad %s Debug Report of %s \n\nTRACEBACK:\n %s \n\nFRAMESTACK:\n" % (self.m.core.server_methods.get_server_version(), pyfile.pluginname, format_exc())

        tb = exc_info()[2]
        stack = []
        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next

        for frame in stack[1:]:

            dump += "\nFrame %s in %s at line %s\n" % (frame.f_code.co_name,
                                                     frame.f_code.co_filename,
                                                     frame.f_lineno)

            for key, value in frame.f_locals.items():
                dump += "\t%20s = " % key
                try:
                    dump += pformat(value) + "\n"
                except Exception, e:
                    dump += "<ERROR WHILE PRINTING VALUE> "+ str(e) +"\n"

        dump += "\n\nPLUGIN OBJECT DUMP: \n\n"

        for name in dir(pyfile.plugin):
            attr = getattr(pyfile.plugin, name)
            if not name.endswith("__") and type(attr) != MethodType:
                dump += "\t%20s = " % name
                try:
                    dump += pformat(attr) + "\n"
                except Exception, e:
                    dump += "<ERROR WHILE PRINTING VALUE> "+ str(e) +"\n"

        dump += "\nPYFILE OBJECT DUMP: \n\n"

        for name in dir(pyfile):
            attr = getattr(pyfile, name)
            if not name.endswith("__") and type(attr) != MethodType:
                dump += "\t%20s = " % name
                try:
                    dump += pformat(attr) + "\n"
                except Exception, e:
                    dump += "<ERROR WHILE PRINTING VALUE> "+ str(e) +"\n"


        if self.m.core.config.plugin.has_key(pyfile.pluginname):
            dump += "\n\nCONFIG: \n\n"
            dump += pformat(self.m.core.config.plugin[pyfile.pluginname]) +"\n"



        dump_name = "debug_%s_%s.txt" % (pyfile.pluginname, strftime("%d-%m-%Y_%H-%M-%S"))
        self.m.core.log.info("Debug Report written to %s" % dump_name)

        f = open(dump_name, "wb")
        f.write(dump)
        f.close()


########################################################################
class DownloadThread(PluginThread):
    """thread for downloading files from 'real' hoster plugins"""

    #----------------------------------------------------------------------
    def __init__(self, manager):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.queue = Queue() # job queue
        self.active = False

        self.start()

    #----------------------------------------------------------------------
    def run(self):
        """run method"""

        while True:
            self.active = self.queue.get()
            pyfile = self.active

            if self.active == "quit":
                self.active = False
                self.m.threads.remove(self)
                return True

            try:
                current = False

                for thread in self.m.threads:
                    if thread == self or not thread.active:
                        continue
                    if thread.active.name == pyfile.name and thread.active.packageid == pyfile.packageid:
                        current = True

                if self.m.core.config["general"]["skip_existing"] and \
                    ((not pyfile.name.startswith("http:") and exists(
                            join(self.m.core.config["general"]["download_folder"], pyfile.package().folder, pyfile.name)
                            )) or current):
                    self.m.log.info(_("Download skipped: %(name)s @ %(plugin)s") % {"name": pyfile.name,
                                                                                    "plugin": pyfile.plugin.__name__
                                                                                    })
                    pyfile.error = _("File already exists.")
                else:

                    self.m.log.info(_("Download starts: %s" % pyfile.name))

                    # start download
                    self.m.core.hookManager.downloadStarts(pyfile)
                    pyfile.plugin.preprocessing(self)

            except NotImplementedError:

                self.m.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
                pyfile.setStatus("failed")
                pyfile.error = "Plugin does not work"
                pyfile.plugin.req.clean()
                self.active = False
                pyfile.release()
                continue

            except Abort:
                self.m.log.info(_("Download aborted: %s") % pyfile.name)
                pyfile.setStatus("aborted")

                pyfile.plugin.req.clean()
                self.active = False
                pyfile.release()
                continue

            except Reconnect:
                self.queue.put(pyfile)
                #pyfile.req.clearCookies()

                while self.m.reconnecting.isSet():
                    sleep(0.5)

                continue

            except Retry:

                self.m.log.info(_("Download restarted: %s") % pyfile.name)
                self.queue.put(pyfile)
                continue

            except Fail, e:

                msg = e.args[0]

                if msg == "offline":
                    pyfile.setStatus("offline")
                    self.m.log.warning(_("Download is offline: %s") % pyfile.name)
                else:
                    pyfile.setStatus("failed")
                    self.m.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                    pyfile.error = msg

                pyfile.plugin.req.clean()
                self.active = False
                pyfile.release()
                continue

            except error, e:
                code, msg = e


                if code in (7,52,56):
                    self.m.log.warning(_("Couldn't connect to host waiting 1 minute and retry."))
                    sleep(60)
                    self.queue.put(pyfile)
                    continue
                else:
                    print "pycurl error", code, msg
                    if self.m.core.debug:
                        print_exc()
                        self.writeDebugReport(pyfile)

                pyfile.plugin.req.clean()
                self.active = False
                pyfile.release()
                continue

            except Exception, e:
                pyfile.setStatus("failed")
                self.m.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": str(e)})
                pyfile.error = str(e)

                if self.m.core.debug:
                    print_exc()
                    self.writeDebugReport(pyfile)

                pyfile.plugin.req.clean()
                self.active = False
                pyfile.release()
                continue


            finally:
                self.m.core.files.save()


            self.m.log.info(_("Download finished: %s") % pyfile.name)
            pyfile.plugin.req.clean()

            self.m.core.hookManager.downloadFinished(pyfile)

            self.m.core.files.checkPackageFinished(pyfile)

            self.active = False
            pyfile.finishIfDone()
            self.m.core.files.save()

    #----------------------------------------------------------------------
    def put(self, job):
        """assing job to thread"""
        self.queue.put(job)

    #----------------------------------------------------------------------
    def stop(self):
        """stops the thread"""
        self.put("quit")



########################################################################
class DecrypterThread(PluginThread):
    """thread for decrypting"""

    #----------------------------------------------------------------------
    def __init__(self, manager, pyfile):
        """constructor"""
        PluginThread.__init__(self, manager)

        self.active = pyfile
        manager.localThreads.append(self)

        pyfile.setStatus("decrypting")

        self.start()

    #----------------------------------------------------------------------
    def run(self):
        """run method"""

        pyfile = self.active

        try:
            self.m.log.info(_("Decrypting starts: %s") % self.active.name)
            self.active.plugin.preprocessing(self)

        except NotImplementedError:

            self.m.log.error(_("Plugin %s is missing a function.") % self.active.pluginname)
            return

        except Fail, e:

            msg = e.args[0]

            if msg == "offline":
                self.active.setStatus("offline")
                self.m.log.warning(_("Download is offline: %s") % self.active.name)
            else:
                self.active.setStatus("failed")
                self.m.log.error(_("Decrypting failed: %(name)s | %(msg)s") % { "name" : self.active.name, "msg":msg })
                self.active.error = msg

            return


        except Exception, e:

            self.active.setStatus("failed")
            self.m.log.error(_("Decrypting failed: %(name)s | %(msg)s") % { "name" : self.active.name, "msg" :str(e) })
            self.active.error = str(e)

            if self.m.core.debug:
                print_exc()
                self.writeDebugReport(pyfile)

            return


        finally:
            self.active.release()
            self.active = False
            self.m.core.files.save()
            self.m.localThreads.remove(self)


        #self.m.core.hookManager.downloadFinished(pyfile)


        #self.m.localThreads.remove(self)
        #self.active.finishIfDone()
        pyfile.delete()

########################################################################
class HookThread(PluginThread):
    """thread for hooks"""

    #----------------------------------------------------------------------
    def __init__(self, m, function, pyfile):
        """Constructor"""
        PluginThread.__init__(self, m)

        self.f = function
        self.active = pyfile

        m.localThreads.append(self)

        if isinstance(pyfile, PyFile):
            pyfile.setStatus("processing")

        self.start()

    def run(self):
        self.f(self.active)


        self.m.localThreads.remove(self)
        if isinstance(self.active, PyFile):
            self.active.finishIfDone()

########################################################################
class InfoThread(PluginThread):

    #----------------------------------------------------------------------
    def __init__(self, manager, data, pid):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.data = data
        self.pid = pid # package id
        # [ .. (name, plugin) .. ]
        self.start()

    #----------------------------------------------------------------------
    def run(self):
        """run method"""

        plugins = {}

        for url, plugin in self.data:
            if plugins.has_key(plugin):
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        for pluginname, urls in plugins.iteritems():
            plugin = self.m.core.pluginManager.getPlugin(pluginname)
            if hasattr(plugin, "getInfo"):
                try:
                    self.m.core.log.debug("Run Info Fetching for %s" % pluginname)
                    for result in plugin.getInfo(urls):
                        if not type(result) == list: result = [result]
                        self.m.core.files.updateFileInfo(result, self.pid)

                    self.m.core.log.debug("Finished Info Fetching for %s" % pluginname)

                    self.m.core.files.save()
                except Exception, e:
                    self.m.core.log.debug("Info Fetching for %s failed | %s" % (pluginname,str) )
                    