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

from pyload.datatype.File import PyFile
from pyload.plugin.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload
from pyload.utils.packagetools import parseNames
from pyload.utils import fs_join
from pyload.api import OnlineStatus


class PluginThread(Thread):
    """abstract base class for thread types"""

    def __init__(self, manager):
        """Constructor"""
        Thread.__init__(self)
        self.setDaemon(True)
        self.m = manager #thread manager


    def writeDebugReport(self, pyfile):
        """ writes a
        :return:
        """

        dump_name = "debug_%s_%s.zip" % (pyfile.pluginname, strftime("%d-%m-%Y_%H-%M-%S"))
        dump = self.getDebugDump(pyfile)

        try:
            import zipfile

            zip = zipfile.ZipFile(dump_name, "w")

            for f in listdir(join("tmp", pyfile.pluginname)):
                try:
                    # avoid encoding errors
                    zip.write(join("tmp", pyfile.pluginname, f), fs_join(pyfile.pluginname, f))
                except Exception:
                    pass

            info = zipfile.ZipInfo(fs_join(pyfile.pluginname, "debug_Report.txt"), gmtime())
            info.external_attr = 0644 << 16L # change permissions

            zip.writestr(info, dump)
            zip.close()

            if not stat(dump_name).st_size:
                raise Exception("Empty Zipfile")

        except Exception, e:
            self.m.log.debug("Error creating zip file: %s" % e)

            dump_name = dump_name.replace(".zip", ".txt")
            f = open(dump_name, "wb")
            f.write(dump)
            f.close()

        self.m.core.log.info("Debug Report written to %s" % dump_name)


    def getDebugDump(self, pyfile):
        dump = "pyLoad %s Debug Report of %s %s \n\nTRACEBACK:\n %s \n\nFRAMESTACK:\n" % (
            self.m.core.api.getServerVersion(), pyfile.pluginname, pyfile.plugin.__version, format_exc())

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

        return dump


    def clean(self, pyfile):
        """ set thread unactive and release pyfile """
        self.active = True  #release pyfile but lets the thread active
        pyfile.release()
