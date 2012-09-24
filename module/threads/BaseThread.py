#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import locale

from threading import Thread
from time import strftime, gmtime
from sys import exc_info
from types import MethodType
from pprint import pformat
from traceback import format_exc

from module.utils.fs import listdir, join, save_join, stat, exists

class BaseThread(Thread):
    """abstract base class for thread types"""

    def __init__(self, manager):
        Thread.__init__(self)
        self.setDaemon(True)
        self.m = manager #thread manager
        self.core = manager.core
        self.log = manager.core.log

    def getProgress(self):
        """ retrieves progress information about the current running task

        :return: :class:`ProgressInfo`
        """

    # Debug Stuff
    def writeDebugReport(self, name, pyfile=None, plugin=None):
        """ writes a debug report to disk  """

        dump_name = "debug_%s_%s.zip" % (name, strftime("%d-%m-%Y_%H-%M-%S"))
        if pyfile:
            dump = self.getFileDump(pyfile)
        else:
            dump = self.getPluginDump(plugin)

        try:
            import zipfile

            zip = zipfile.ZipFile(dump_name, "w")

            if exists(join("tmp", name)):
                for f in listdir(join("tmp", name)):
                    try:
                        # avoid encoding errors
                        zip.write(join("tmp", name, f), save_join(name, f))
                    except:
                        pass

            info = zipfile.ZipInfo(save_join(name, "debug_Report.txt"), gmtime())
            info.external_attr = 0644 << 16L # change permissions
            zip.writestr(info, dump)

            info = zipfile.ZipInfo(save_join(name, "system_Report.txt"), gmtime())
            info.external_attr = 0644 << 16L
            zip.writestr(info, self.getSystemDump())

            zip.close()

            if not stat(dump_name).st_size:
                raise Exception("Empty Zipfile")

        except Exception, e:
            self.log.debug("Error creating zip file: %s" % e)

            dump_name = dump_name.replace(".zip", ".txt")
            f = open(dump_name, "wb")
            f.write(dump)
            f.close()

        self.log.info("Debug Report written to %s" % dump_name)
        return dump_name

    def getFileDump(self, pyfile):
        dump = "pyLoad %s Debug Report of %s %s \n\nTRACEBACK:\n %s \n\nFRAMESTACK:\n" % (
            self.m.core.api.getServerVersion(), pyfile.pluginname, pyfile.plugin.__version__, format_exc())

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

        dump += "\n\nCONFIG: \n\n"
        dump += pformat(self.m.core.config.values) + "\n"

        return dump

        #TODO
    def getPluginDump(self, plugin):
        return ""

    def getSystemDump(self):
        return ""
