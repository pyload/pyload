# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import str
import io
import os
import time
import zipfile

from future import standard_library
standard_library.install_aliases()

from pyload.utils import debug, format, sys
from pyload.utils.layer.safethreading import Thread
from pyload.utils.path import filesize, makedirs, open


class PluginThread(Thread):
    """
    Abstract base class for thread types.
    """
    __slots__ = ['manager', 'owner', 'pyload']

    def __init__(self, manager, owner=None):
        """
        Constructor
        """
        Thread.__init__(self)
        self.setDaemon(True)
        self.manager = manager  #: Thread manager
        self.pyload  = manager.pyload
        #: Owner of the thread, every type should set it or overwrite user
        self.owner = owner

    @property
    def user(self):
        return self.owner.primary if self.owner else None

    @property
    def progress(self):
        return self.get_progress()

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
        pass

    def _debug_report(self, file):
        # TODO: Add config setting dump
        report = "pyLoad {} Debug Report of {} {}\n\n{}\n\n{}\n\n{}\n\n{}".format(
            self.pyload.__version__,
            file.plugin.__name__,
            file.plugin.__version__,
            debug.format_traceback(),
            debug.format_framestack(),
            debug.format_dump(file.plugin),
            debug.format_dump(file)
        )
        return report

    def _write_report(self, report, path):
        with zipfile.ZipFile(path, 'w') as zip:
            reportdir = os.path.join(
                self.pyload.profiledir, 'crashes', 'reports', name)  # NOTE: Relpath to configdir
            makedirs(reportdir)

            for fname in os.listdir(reportdir):
                try:
                    zip.write(os.path.join(reportdir, fname),
                              os.path.join(name, fname))
                except Exception:
                    pass

            for name, data in (('debug', report), ('system', system)):
                info = zipfile.ZipInfo(
                    os.path.join(name, "{0}_Report.txt".format(name)), time.gmtime())
                info.external_attr = 0o644 << 16  #: change permissions
                zip.writestr(info, data)

        if not filesize(path):
            raise Exception("Empty Zipfile")

    def debug_report(self, file):
        """
        Writes a debug report to disk.
        """
        name = file.pluginname
        path = "debug_{}_{}.zip".format(
            name, time.strftime("%d-%m-%Y_%H-%M-%S"))

        report = self._debug_report(file)
        system = "SYSTEM INFO:\n\t{}\n".format(
            '\n\t'.join(format.map(sys.get_info())))
        try:
            self._write_report(report, path)

        except Exception as e:
            self.pyload.log.debug("Error creating zip file", str(e))
            path = path.replace(".zip", ".txt")
            with io.open(path, mode='wb') as fp:
                fp.write(report)

        self.pyload.log.info(_("Debug Report written to file"), path)
