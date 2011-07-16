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
from time import time
from time import strftime
from traceback import print_exc, format_exc
from pprint import pformat
from sys import exc_info, exc_clear
from types import MethodType

from pycurl import error

from PyFile import PyFile
from plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload
from common.packagetools import parseNames
from remote.thriftbackend.thriftgen.pyload.ttypes import OnlineStatus


class PluginThread(Thread):
    """abstract base class for thread types"""

    #----------------------------------------------------------------------
    def __init__(self, manager):
        """Constructor"""
        Thread.__init__(self)
        self.setDaemon(True)
        self.m = manager #thread manager


    def writeDebugReport(self, pyfile):
        dump = "pyLoad %s Debug Report of %s \n\nTRACEBACK:\n %s \n\nFRAMESTACK:\n" % (
            self.m.core.api.getServerVersion(), pyfile.pluginname, format_exc())

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
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

            del frame

        del stack #delete it just to be sure...

        dump += "\n\nPLUGIN OBJECT DUMP: \n\n"

        for name in dir(pyfile.plugin):
            attr = getattr(pyfile.plugin, name)
            if not name.endswith("__") and type(attr) != MethodType:
                dump += "\t%20s = " % name
                try:
                    dump += pformat(attr) + "\n"
                except Exception, e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

        dump += "\nPYFILE OBJECT DUMP: \n\n"

        for name in dir(pyfile):
            attr = getattr(pyfile, name)
            if not name.endswith("__") and type(attr) != MethodType:
                dump += "\t%20s = " % name
                try:
                    dump += pformat(attr) + "\n"
                except Exception, e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

        if pyfile.pluginname in self.m.core.config.plugin:
            dump += "\n\nCONFIG: \n\n"
            dump += pformat(self.m.core.config.plugin[pyfile.pluginname]) + "\n"

        dump_name = "debug_%s_%s.txt" % (pyfile.pluginname, strftime("%d-%m-%Y_%H-%M-%S"))
        self.m.core.log.info("Debug Report written to %s" % dump_name)

        f = open(dump_name, "wb")
        f.write(dump)
        f.close()

    def clean(self, pyfile):
        """ set thread unactive and release pyfile """
        self.active = False
        pyfile.release()


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
                if not pyfile.hasPlugin(): continue
                #this pyfile was deleted while queueing

                pyfile.plugin.checkForSameFiles(starting=True)
                self.m.log.info(_("Download starts: %s" % pyfile.name))

                # start download
                self.m.core.hookManager.downloadStarts(pyfile)
                pyfile.plugin.preprocessing(self)

            except NotImplementedError:
                self.m.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
                pyfile.setStatus("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.m.log.info(_("Download aborted: %s") % pyfile.name)
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

                self.clean(pyfile)
                continue

            except error, e:
                try:
                    code, msg = e.args
                except:
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

                self.clean(pyfile)
                continue

            finally:
                self.m.core.files.save()
                self.m.core.files.checkAllLinksProcessed()
                exc_clear()

            self.m.log.info(_("Download finished: %s") % pyfile.name)
            #pyfile.plugin.req.clean()

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
        retry = False

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
                self.m.log.error(_("Decrypting failed: %(name)s | %(msg)s") % {"name": self.active.name, "msg": msg})
                self.active.error = msg

            return

        except Abort:
            self.m.log.info(_("Download aborted: %s") % pyfile.name)
            pyfile.setStatus("aborted")

            return

        except Retry:
            self.m.log.info(_("Retrying %s") % self.active.name)
            retry = True
            return self.run()

        except Exception, e:
            self.active.setStatus("failed")
            self.m.log.error(_("Decrypting failed: %(name)s | %(msg)s") % {"name": self.active.name, "msg": str(e)})
            self.active.error = str(e)

            if self.m.core.debug:
                print_exc()
                self.writeDebugReport(pyfile)

            return


        finally:
            if not retry:
                self.active.release()
                self.active = False
                self.m.core.files.save()
                self.m.localThreads.remove(self)
                exc_clear()


        #self.m.core.hookManager.downloadFinished(pyfile)


        #self.m.localThreads.remove(self)
        #self.active.finishIfDone()
        if not retry:
            pyfile.delete()


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


class InfoThread(PluginThread):
    def __init__(self, manager, data, pid=-1, rid=-1):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.data = data
        self.pid = pid # package id
        # [ .. (name, plugin) .. ]

        self.rid = rid #result id

        self.cache = [] #accumulated data

        self.start()

    def run(self):
        """run method"""

        plugins = {}

        for url, plugin in self.data:
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        #directly write to database
        if self.pid > -1:
            for pluginname, urls in plugins.iteritems():
                plugin = self.m.core.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateDB)
                    self.m.core.files.save()

        else: #post the results

            self.m.infoResults[self.rid] = {}

            for pluginname, urls in plugins.iteritems():
                plugin = self.m.core.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateResult, True)

                    #force to process cache
                    if self.cache:
                        self.updateResult(pluginname, [], True)

                else:
                    #generate default result
                    tmp = [(url, (url, OnlineStatus(url, pluginname, 3, 0))) for url in urls]
                    result = parseNames(tmp)
                    for k in result.iterkeys():
                        result[k] = dict(result[k])

                    self.m.setInfoResults(self.rid, result)

            self.m.infoResults[self.rid]["ALL_INFO_FETCHED"] = {}

        self.m.timestamp = time() + 5 * 60


    def updateDB(self, plugin, result):
        self.m.core.files.updateFileInfo(result, self.pid)

    def updateResult(self, plugin, result, force=False):
        #parse package name and generate result
        #accumulate results

        self.cache.extend(result)

        if len(self.cache) >= 20 or force:
            #used for package generating
            tmp = [(name, (url, OnlineStatus(name, plugin, status, int(size))))
            for name, size, status, url in self.cache]

            result = parseNames(tmp)
            for k in result.iterkeys():
                result[k] = dict(result[k])

            self.m.setInfoResults(self.rid, result)

            self.cache = []

    def fetchForPlugin(self, pluginname, plugin, urls, cb, err=None):
        try:
            result = [] #result loaded from cache
            process = [] #urls to process
            for url in urls:
                if url in self.m.infoCache:
                    result.append(self.m.infoCache[url])
                else:
                    process.append(url)

            if result:
                self.m.core.log.debug("Fetched %d values from cache for %s" % (len(result), pluginname))
                cb(pluginname, result)

            if process:
                self.m.core.log.debug("Run Info Fetching for %s" % pluginname)
                for result in plugin.getInfo(process):
                    #result = [ .. (name, size, status, url) .. ]
                    if not type(result) == list: result = [result]

                    for res in result:
                        self.m.infoCache[res[3]] = res

                    cb(pluginname, result)

            self.m.core.log.debug("Finished Info Fetching for %s" % pluginname)
        except Exception, e:
            self.m.core.log.warning(_("Info Fetching for %(name)s failed | %(err)s") %
                                    {"name": pluginname, "err": str(e)})
            if self.m.core.debug:
                print_exc()

            #TODO: generate default results
            if err:
                pass
