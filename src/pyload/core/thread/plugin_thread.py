# -*- coding: utf-8 -*-
# AUTHOR: RaNaN

import os
import pprint
import time
import traceback
from sys import exc_info
from threading import Thread
from types import MethodType


class PluginThread(Thread):
    """
    abstract base class for thread types.
    """

    # ----------------------------------------------------------------------
    def __init__(self, manager):
        """
        Constructor.
        """
        super().__init__()
        self.daemon = True
        self.pyload = manager.pyload
        self._ = manager._
        self.m = self.manager = manager  #: thread manager

    def writeDebugReport(self, pyfile):
        """
        writes a.

        :return:
        """
        date = time.strftime("%Y-%m-%d_%H-%M-%S")
        dump_name = f"debug_{pyfile.pluginname}_{date}.zip"
        dump = self.getDebugDump(pyfile)

        try:
            import zipfile

            with zipfile.ZipFile(dump_name, "w") as zip:
                for f in os.listdir(
                    os.path.join(self.pyload.cachedir, pyfile.pluginname)
                ):
                    try:
                        # avoid encoding errors
                        zip.write(
                            os.path.join(self.pyload.cachedir, pyfile.pluginname, f),
                            os.path.join(pyfile.pluginname, f),
                        )
                    except Exception:
                        pass

                info = zipfile.ZipInfo(
                    os.path.join(pyfile.pluginname, "debug_Report.txt"), time.gmtime()
                )
                info.external_attr = 0o644 << 16  #: change permissions

                zip.writestr(info, dump)

            if not os.stat(dump_name).st_size:
                raise Exception("Empty Zipfile")

        except Exception as exc:
            self.pyload.log.debug(f"Error creating zip file: {exc}")

            dump_name = dump_name.replace(".zip", ".txt")
            with open(dump_name, mode="wb") as f:
                f.write(dump)

        self.pyload.log.info(self._("Debug Report written to {}").format(dump_name))

    def getDebugDump(self, pyfile):
        version = self.m.pyload.api.getServerVersion()
        dump = f"pyLoad {version} Debug Report of {pyfile.pluginname} {pyfile.plugin.__version__} \n\nTRACEBACK:\n {traceback.format_exc()} \n\nFRAMESTACK:\n"

        tb = exc_info()[2]
        stack = []
        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next

        for frame in stack[1:]:
            dump += f"\nFrame {frame.f_code.co_name} in {frame.f_code.co_filename} at line {frame.f_lineno}\n"

            for key, value in frame.f_locals.items():
                dump += "\t{:20} = ".format(key)
                try:
                    dump += pprint.pformat(value) + "\n"
                except Exception as exc:
                    dump += f"<ERROR WHILE PRINTING VALUE> {exc}\n"

            del frame

        del stack  #: delete it just to be sure...

        dump += "\n\nPLUGIN OBJECT DUMP: \n\n"

        for name in dir(pyfile.plugin):
            attr = getattr(pyfile.plugin, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t{:20} = ".format(name)
                try:
                    dump += pprint.pformat(attr) + "\n"
                except Exception as exc:
                    dump += f"<ERROR WHILE PRINTING VALUE> {exc}\n"

        dump += "\nPYFILE OBJECT DUMP: \n\n"

        for name in dir(pyfile):
            attr = getattr(pyfile, name)
            if not name.endswith("__") and not isinstance(attr, MethodType):
                dump += "\t{:20} = ".format(name)
                try:
                    dump += pprint.pformat(attr) + "\n"
                except Exception as exc:
                    dump += f"<ERROR WHILE PRINTING VALUE> {exc}\n"

        if pyfile.pluginname in self.m.pyload.config.plugin:
            dump += "\n\nCONFIG: \n\n"
            dump += (
                pprint.pformat(self.m.pyload.config.plugin[pyfile.pluginname]) + "\n"
            )

        return dump

    def clean(self, pyfile):
        """
        set thread unactive and release pyfile.
        """
        self.active = False
        pyfile.release()
