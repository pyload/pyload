# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
from contextlib import closing
from pprint import pformat
from time import gmtime, strftime
from traceback import format_exc

from pyload.utils.lib.threading import Thread
from pyload.utils.old.fs import exists, join, listdir, save_join, stat
from types import MethodType

from ..setup.system import get_system_info


class BaseThread(Thread):
    """
    Abstract base class for thread types.
    """

    def __init__(self, manager, owner=None):
        Thread.__init__(self)
        self.setDaemon(True)
        self.manager = manager  # thread manager
        self.pyload = manager.pyload

        #: Owner of the thread, every type should set it or overwrite user
        self.owner = owner

    @property
    def user(self):
        return self.owner.primary if self.owner else None

    def finished(self):
        """
        Remove thread from list.
        """
        self.manager.remove_thread(self)

    def get_progress(self):
        """
        Retrieves progress information about the current running task

        :return: :class:`ProgressInfo`
        """

    # Debug Stuff
    def write_debug_report(self, name, pyfile=None, plugin=None):
        """
        Writes a debug report to disk.
        """
        dump_name = "debug_{}_{}.zip".format(
            name, strftime("%d-%m-%Y_%H-%M-%S"))
        if pyfile:
            dump = self.get_plugin_dump(pyfile.plugin) + "\n"
            dump += self.get_file_dump(pyfile)
        else:
            dump = self.get_plugin_dump(plugin)

        try:
            import zipfile
            with closing(zipfile.ZipFile(dump_name, "w")) as zip:
                if exists(join("tmp", name)):
                    for f in listdir(join("tmp", name)):
                        try:
                            # avoid encoding errors
                            zip.write(join("tmp", name, f), save_join(name, f))
                        except Exception:
                            pass

                info = zipfile.ZipInfo(
                    save_join(name, "debug_Report.txt"), gmtime())
                info.external_attr = 0o644 << 16  # change permissions
                zip.writestr(info, dump)

                info = zipfile.ZipInfo(
                    save_join(name, "system_Report.txt"), gmtime())
                info.external_attr = 0o644 << 16
                zip.writestr(info, self.get_system_dump())

            if not stat(dump_name).st_size:
                raise Exception("Empty Zipfile")

        except Exception as e:
            self.pyload.log.debug(
                "Error creating zip file: {}".format(e.message))

            dump_name = dump_name.replace(".zip", ".txt")
            with open(dump_name, "wb") as f:
                f.write(dump)

        self.pyload.log.info(_("Debug Report written to {}").format(dump_name))
        return dump_name

    def get_plugin_dump(self, plugin):
        dump = "pyLoad {} Debug Report of {} {} \n\nTRACEBACK:\n {} \n\nFRAMESTACK:\n".format(
            self.manager.pyload.api.get_server_version(
            ), plugin.__name__, plugin.__version__, format_exc()
        )
        tb = sys.exc_info()[2]
        stack = []
        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next

        for frame in stack[1:]:
            dump += "\nFrame {} in {} at line {}\n".format(frame.f_code.co_name,
                                                           frame.f_code.co_filename,
                                                           frame.f_lineno)

            for key, value in frame.f_locals.items():
                dump += "\t{:20} = ".format(key)
                try:
                    dump += pformat(value) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> {}\n".format(
                        e.message)

            del frame

        del stack  # delete it just to be sure...

        dump += "\n\nPLUGIN OBJECT DUMP: \n\n"

        for name in dir(plugin):
            attr = getattr(plugin, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t{:20} = ".format(name)
                try:
                    dump += pformat(attr) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> {}\n".format(
                        e.message)

        return dump

    def get_file_dump(self, pyfile):
        dump = "PYFILE OBJECT DUMP: \n\n"

        for name in dir(pyfile):
            attr = getattr(pyfile, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t{:20} = ".format(name)
                try:
                    dump += pformat(attr) + "\n"
                except Exception as e:
                    dump += "<ERROR WHILE PRINTING VALUE> {}\n".format(
                        e.message)

        return dump

    def get_system_dump(self):
        dump = "SYSTEM:\n\n"
        for k, v in get_system_info().items():
            dump += "{}: {}\n".format(k, v)

        return dump
