# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import str
import sys
from threading import Thread
from time import strftime, gmtime
from types import MethodType
from pprint import pformat
from traceback import format_exc

from pyload.utils import primary_uid
from pyload.utils.fs import listdir, join, save_join, stat, exists
from pyload.setup.system import get_system_info


class BaseThread(Thread):
    """abstract base class for thread types"""

    def __init__(self, manager, owner=None):
        Thread.__init__(self)
        self.setDaemon(True)
        self.manager = manager #thread manager
        self.pyload = manager.pyload
        self.log = manager.pyload.log

        #: Owner of the thread, every type should set it or overwrite user
        self.owner = owner

    @property
    def user(self):
        return primary_uid(self.owner)

    def finished(self):
        """ Remove thread from list  """
        self.manager.remove_thread(self)

    def get_progress(self):
        """ retrieves progress information about the current running task

        :return: :class:`ProgressInfo`
        """

    # Debug Stuff
    def write_debug_report(self, name, pyfile=None, plugin=None):
        """ writes a debug report to disk  """

        dump_name = "debug_%s_%s.zip" % (name, strftime("%d-%m-%Y_%H-%M-%S"))
        if pyfile:
            dump = self.get_plugin_dump(pyfile.plugin) + "\n"
            dump += self.get_file_dump(pyfile)
        else:
            dump = self.get_plugin_dump(plugin)

        try:
            import zipfile
            zip = zipfile.ZipFile(dump_name, "w")

            if exists(join("tmp", name)):
                for f in listdir(join("tmp", name)):
                    try:
                        # avoid encoding errors
                        zip.write(join("tmp", name, f), save_join(name, f))
                    except Exception:
                        pass

            info = zipfile.ZipInfo(save_join(name, "debug_Report.txt"), gmtime())
            info.external_attr = 0o644 << 16 # change permissions
            zip.writestr(info, dump)

            info = zipfile.ZipInfo(save_join(name, "system_Report.txt"), gmtime())
            info.external_attr = 0o644 << 16
            zip.writestr(info, self.get_system_dump())

            zip.close()

            if not stat(dump_name).st_size:
                raise Exception("Empty Zipfile")

        except Exception as e:
            self.log.debug("Error creating zip file: %s" % e)

            dump_name = dump_name.replace(".zip", ".txt")
            f = open(dump_name, "wb")
            f.write(dump)
            f.close()

        self.log.info("Debug Report written to %s" % dump_name)
        return dump_name

    def get_plugin_dump(self, plugin):
        dump = "pyLoad %s Debug Report of %s %s \n\nTRACEBACK:\n %s \n\nFRAMESTACK:\n" % (
            self.manager.pyload.api.get_server_version(), plugin.__name__, plugin.__version__, format_exc())

        tb = sys.exc_info()[2]
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
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

            del frame

        del stack #delete it just to be sure...

        dump += "\n\nPLUGIN OBJECT DUMP: \n\n"

        for name in dir(plugin):
            attr = getattr(plugin, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t%20s = " % name
                try:
                    dump += pformat(attr) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

        return dump

    def get_file_dump(self, pyfile):
        dump = "PYFILE OBJECT DUMP: \n\n"

        for name in dir(pyfile):
            attr = getattr(pyfile, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t%20s = " % name
                try:
                    dump += pformat(attr) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> " + str(e) + "\n"

        return dump

    def get_system_dump(self):
        dump = "SYSTEM:\n\n"
        for k, v in get_system_info().items():
            dump += "%s: %s\n" % (k, v)

        return dump
