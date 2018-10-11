# -*- coding: utf-8 -*-
from builtins import _
# @author: RaNaN

from builtins import _, str
from copy import copy
from os import listdir, stat
from os.path import join
from pprint import pformat
from queue import Queue
from sys import exc_clear, exc_info
from threading import Thread
from time import gmtime, sleep, strftime, time
from traceback import format_exc, print_exc
from types import MethodType

from pycurl import error
from pyload.Api import OnlineStatus
from pyload.datatype.PyFile import PyFile
from pyload.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload
from pyload.utils.utils import save_join
from pyload.utils.utils.packagetools import parseNames


class PluginThread(Thread):
    """abstract base class for thread types"""

    # ----------------------------------------------------------------------
    def __init__(self, manager):
        """Constructor"""
        Thread.__init__(self)
        self.setDaemon(True)
        self.m = manager  # thread manager

    def writeDebugReport(self, pyfile):
        """ writes a
        :return:
        """

        dump_name = "debug_{}_{}.zip".format(
            pyfile.pluginname, strftime("%d-%m-%Y_%H-%M-%S"))
        dump = self.getDebugDump(pyfile)

        try:
            import zipfile

            zip = zipfile.ZipFile(dump_name, "w")

            for f in listdir(join("tmp", pyfile.pluginname)):
                try:
                    # avoid encoding errors
                    zip.write(
                        join(
                            "tmp", pyfile.pluginname, f), save_join(
                            pyfile.pluginname, f))
                except Exception:
                    pass

            info = zipfile.ZipInfo(
                save_join(
                    pyfile.pluginname,
                    "debug_Report.txt"),
                gmtime())
            info.external_attr = 0o644 << 16  # change permissions

            zip.writestr(info, dump)
            zip.close()

            if not stat(dump_name).st_size:
                raise Exception("Empty Zipfile")

        except Exception as e:
            self.m.log.debug("Error creating zip file: {}".format(e))

            dump_name = dump_name.replace(".zip", ".txt")
            f = open(dump_name, "wb")
            f.write(dump)
            f.close()

        self.m.core.log.info("Debug Report written to {}".format(dump_name))

    def getDebugDump(self, pyfile):
        dump = "pyLoad {} Debug Report of {} {} \n\nTRACEBACK:\n {} \n\nFRAMESTACK:\n".format(
            self.m.core.api.getServerVersion(), pyfile.pluginname, pyfile.plugin.__version__, format_exc())

        tb = exc_info()[2]
        stack = []
        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next

        for frame in stack[1:]:
            dump += "\nFrame {} in {} at line {}\n".format(frame.f_code.co_name,
                                                           frame.f_code.co_filename,
                                                           frame.f_lineno)

            for key, value in list(frame.f_locals.items()):
                dump += "\t{:20} = ".format(key)
                try:
                    dump += pformat(value) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

            del frame

        del stack  # delete it just to be sure...

        dump += "\n\nPLUGIN OBJECT DUMP: \n\n"

        for name in dir(pyfile.plugin):
            attr = getattr(pyfile.plugin, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t{:20} = ".format(name)
                try:
                    dump += pformat(attr) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

        dump += "\nPYFILE OBJECT DUMP: \n\n"

        for name in dir(pyfile):
            attr = getattr(pyfile, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t{:20} = ".format(name)
                try:
                    dump += pformat(attr) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

        if pyfile.pluginname in self.m.core.config.plugin:
            dump += "\n\nCONFIG: \n\n"
            dump += pformat(self.m.core.config.plugin[pyfile.pluginname]) + "\n"

        return dump

    def clean(self, pyfile):
        """ set thread unactive and release pyfile """
        self.active = False
        pyfile.release()


class DownloadThread(PluginThread):
    """thread for downloading files from 'real' hoster plugins"""

    # ----------------------------------------------------------------------
    def __init__(self, manager):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.queue = Queue()  # job queue
        self.active = False

        self.start()

    # ----------------------------------------------------------------------
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
                # this pyfile was deleted while queueing

                pyfile.plugin.checkForSameFiles(starting=True)
                self.m.log.info(_("Download starts: {}".format(pyfile.name)))

                # start download
                self.m.core.hookManager.downloadPreparing(pyfile)
                pyfile.plugin.preprocessing(self)

                self.m.log.info(_("Download finished: {}").format(pyfile.name))
                self.m.core.hookManager.downloadFinished(pyfile)
                self.m.core.files.checkPackageFinished(pyfile)

            except NotImplementedError:
                self.m.log.error(
                    _("Plugin {} is missing a function.").format(
                        pyfile.pluginname))
                pyfile.setStatus("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.m.log.info(_("Download aborted: {}").format(pyfile.name))
                except Exception:
                    pass

                pyfile.setStatus("aborted")

                self.clean(pyfile)
                continue

            except Reconnect:
                self.queue.put(pyfile)
                # pyfile.req.clearCookies()

                while self.m.reconnecting.isSet():
                    sleep(0.5)

                continue

            except Retry as e:
                reason = e.args[0]
                self.m.log.info(_("Download restarted: {name} | {msg}").format(
                    **{"name": pyfile.name, "msg": reason}))
                self.queue.put(pyfile)
                continue

            except Fail as e:
                msg = e.args[0]

                if msg == "offline":
                    pyfile.setStatus("offline")
                    self.m.log.warning(_("Download is offline: {}").format(pyfile.name))
                elif msg == "temp. offline":
                    pyfile.setStatus("temp. offline")
                    self.m.log.warning(
                        _("Download is temporary offline: {}").format(
                            pyfile.name))
                else:
                    pyfile.setStatus("failed")
                    self.m.log.warning(_("Download failed: {name} | {msg}").format(
                        **{"name": pyfile.name, "msg": msg}))
                    pyfile.error = msg

                self.m.core.hookManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            except error as e:
                if len(e.args) == 2:
                    code, msg = e.args
                else:
                    code = 0
                    msg = e.args

                self.m.log.debug("pycurl exception {}: {}".format(code, msg))

                if code in (7, 18, 28, 52, 56):
                    self.m.log.warning(
                        _("Couldn't connect to host or connection reset, waiting 1 minute and retry."))
                    wait = time() + 60

                    pyfile.waitUntil = wait
                    pyfile.setStatus("waiting")
                    while time() < wait:
                        sleep(1)
                        if pyfile.abort:
                            break

                    if pyfile.abort:
                        self.m.log.info(_("Download aborted: {}").format(pyfile.name))
                        pyfile.setStatus("aborted")

                        self.clean(pyfile)
                    else:
                        self.queue.put(pyfile)

                    continue

                else:
                    pyfile.setStatus("failed")
                    self.m.log.error("pycurl error {}: {}".format(code, msg))
                    if self.m.core.debug:
                        print_exc()
                        self.writeDebugReport(pyfile)

                    self.m.core.hookManager.downloadFailed(pyfile)

                self.clean(pyfile)
                continue

            except SkipDownload as e:
                pyfile.setStatus("skipped")

                self.m.log.info(_("Download skipped: {name} due to {plugin}").format(
                    **{"name": pyfile.name, "plugin": e.message}))

                self.clean(pyfile)

                self.m.core.files.checkPackageFinished(pyfile)

                self.active = False
                self.m.core.files.save()

                continue

            except Exception as e:
                pyfile.setStatus("failed")
                self.m.log.warning(_("Download failed: {name} | {msg}").format(
                    **{"name": pyfile.name, "msg": str(e)}))
                pyfile.error = str(e)

                if self.m.core.debug:
                    print_exc()
                    self.writeDebugReport(pyfile)

                self.m.core.hookManager.downloadFailed(pyfile)
                self.clean(pyfile)
                continue

            finally:
                self.m.core.files.save()
                pyfile.checkIfProcessed()
                exc_clear()

            # pyfile.plugin.req.clean()

            self.active = False
            pyfile.finishIfDone()
            self.m.core.files.save()

    def put(self, job):
        """assing job to thread"""
        self.queue.put(job)

    def stop(self):
        """stops the thread"""
        self.put("quit")


class DecrypterThread(PluginThread):
    """thread for decrypting"""

    def __init__(self, manager, pyfile):
        """constructor"""
        PluginThread.__init__(self, manager)

        self.active = pyfile
        manager.localThreads.append(self)

        pyfile.setStatus("decrypting")

        self.start()

    def getActiveFiles(self):
        return [self.active]

    def run(self):
        """run method"""

        pyfile = self.active
        retry = False

        try:
            self.m.log.info(_("Decrypting starts: {}").format(self.active.name))
            self.active.plugin.preprocessing(self)

        except NotImplementedError:
            self.m.log.error(
                _("Plugin {} is missing a function.").format(
                    self.active.pluginname))
            return

        except Fail as e:
            msg = e.args[0]

            if msg == "offline":
                self.active.setStatus("offline")
                self.m.log.warning(
                    _("Download is offline: {}").format(
                        self.active.name))
            else:
                self.active.setStatus("failed")
                self.m.log.error(_("Decrypting failed: {name} | {msg}").format(
                    **{"name": self.active.name, "msg": msg}))
                self.active.error = msg

            return

        except Abort:
            self.m.log.info(_("Download aborted: {}").format(pyfile.name))
            pyfile.setStatus("aborted")

            return

        except Retry:
            self.m.log.info(_("Retrying {}").format(self.active.name))
            retry = True
            return self.run()

        except Exception as e:
            self.active.setStatus("failed")
            self.m.log.error(_("Decrypting failed: {name} | {msg}").format(
                **{"name": self.active.name, "msg": str(e)}))
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

        # self.m.core.hookManager.downloadFinished(pyfile)

        # self.m.localThreads.remove(self)
        # self.active.finishIfDone()
        if not retry:
            pyfile.delete()


class HookThread(PluginThread):
    """thread for addons"""

    # ----------------------------------------------------------------------
    def __init__(self, m, function, args, kwargs):
        """Constructor"""
        PluginThread.__init__(self, m)

        self.f = function
        self.args = args
        self.kwargs = kwargs

        self.active = []

        m.localThreads.append(self)

        self.start()

    def getActiveFiles(self):
        return self.active

    def addActive(self, pyfile):
        """ Adds a pyfile to active list and thus will be displayed on overview"""
        if pyfile not in self.active:
            self.active.append(pyfile)

    def finishFile(self, pyfile):
        if pyfile in self.active:
            self.active.remove(pyfile)

        pyfile.finishIfDone()

    def run(self):
        try:
            try:
                self.kwargs["thread"] = self
                self.f(*self.args, **self.kwargs)
            except TypeError as e:
                # dirty method to filter out exceptions
                if "unexpected keyword argument 'thread'" not in e.args[0]:
                    raise

                del self.kwargs["thread"]
                self.f(*self.args, **self.kwargs)
        finally:
            local = copy(self.active)
            for x in local:
                self.finishFile(x)

            self.m.localThreads.remove(self)


class InfoThread(PluginThread):
    def __init__(self, manager, data, pid=-1, rid=-1, add=False):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.data = data
        self.pid = pid  # package id
        # [ .. (name, plugin) .. ]

        self.rid = rid  # result id
        self.add = add  # add packages instead of return result

        self.cache = []  # accumulated data

        self.start()

    def run(self):
        """run method"""

        plugins = {}
        container = []

        for url, plugin in self.data:
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        # filter out container plugins
        for name in self.m.core.pluginManager.containerPlugins:
            if name in plugins:
                container.extend([(name, url) for url in plugins[name]])

                del plugins[name]

        # directly write to database
        if self.pid > -1:
            for pluginname, urls in plugins.items():
                plugin = self.m.core.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateDB)
                    self.m.core.files.save()

        elif self.add:
            for pluginname, urls in plugins.items():
                plugin = self.m.core.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(
                        pluginname, plugin, urls, self.updateCache, True)

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateCache(pluginname, result)

            packs = parseNames([(name, url) for name, x, y, url in self.cache])

            self.m.log.debug("Fetched and generated {:d} packages".format(len(packs)))

            for k, v in packs:
                self.m.core.api.addPackage(k, v)

            # empty cache
            del self.cache[:]

        else:  # post the results

            for name, url in container:
                # attach container content
                try:
                    data = self.decryptContainer(name, url)
                except Exception:
                    print_exc()
                    self.m.log.error("Could not decrypt container.")
                    data = []

                for url, plugin in data:
                    if plugin in plugins:
                        plugins[plugin].append(url)
                    else:
                        plugins[plugin] = [url]

            self.m.infoResults[self.rid] = {}

            for pluginname, urls in plugins.items():
                plugin = self.m.core.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(
                        pluginname, plugin, urls, self.updateResult, True)

                    # force to process cache
                    if self.cache:
                        self.updateResult(pluginname, [], True)

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateResult(pluginname, result, True)

            self.m.infoResults[self.rid]["ALL_INFO_FETCHED"] = {}

        self.m.timestamp = time() + 5 * 60

    def updateDB(self, plugin, result):
        self.m.core.files.updateFileInfo(result, self.pid)

    def updateResult(self, plugin, result, force=False):
        # parse package name and generate result
        # accumulate results

        self.cache.extend(result)

        if len(self.cache) >= 20 or force:
            # used for package generating
            tmp = [(name, (url, OnlineStatus(name, plugin, "unknown", status, int(size))))
                   for name, size, status, url in self.cache]

            data = parseNames(tmp)
            result = {}
            for k, v in data.items():
                for url, status in v:
                    status.packagename = k
                    result[url] = status

            self.m.setInfoResults(self.rid, result)

            self.cache = []

    def updateCache(self, plugin, result):
        self.cache.extend(result)

    def fetchForPlugin(self, pluginname, plugin, urls, cb, err=None):
        try:
            result = []  # result loaded from cache
            process = []  # urls to process
            for url in urls:
                if url in self.m.infoCache:
                    result.append(self.m.infoCache[url])
                else:
                    process.append(url)

            if result:
                self.m.log.debug(
                    "Fetched {:d} values from cache for {}".format(
                        len(result), pluginname))
                cb(pluginname, result)

            if process:
                self.m.log.debug("Run Info Fetching for {}".format(pluginname))
                for result in plugin.getInfo(process):
                    # result = [ .. (name, size, status, url) .. ]
                    if not isinstance(result, list):
                        result = [result]

                    for res in result:
                        self.m.infoCache[res[3]] = res

                    cb(pluginname, result)

            self.m.log.debug("Finished Info Fetching for {}".format(pluginname))
        except Exception as e:
            self.m.log.warning(_("Info Fetching for {name} failed | {err}").format(**{"name": pluginname, "err": str(e)}))
            if self.m.core.debug:
                print_exc()

            # generate default results
            if err:
                result = [(url, 0, 3, url) for url in urls]
                cb(pluginname, result)

    def decryptContainer(self, plugin, url):
        data = []
        # only works on container plugins

        self.m.log.debug("Pre decrypting {} with {}".format(url, plugin))

        # dummy pyfile
        pyfile = PyFile(self.m.core.files, -1, url, url, 0, 0, "", plugin, -1, -1)

        pyfile.initPlugin()

        # little plugin lifecycle
        try:
            pyfile.plugin.setup()
            pyfile.plugin.loadToDisk()
            pyfile.plugin.decrypt(pyfile)
            pyfile.plugin.deleteTmp()

            for pack in pyfile.plugin.packages:
                pyfile.plugin.urls.extend(pack[1])

            data = self.m.core.pluginManager.parseUrls(pyfile.plugin.urls)

            self.m.log.debug("Got {:d} links.".format(len(data)))

        except Exception as e:
            self.m.log.debug("Pre decrypting error: {}".format(str(e)))
        finally:
            pyfile.release()

        return data
