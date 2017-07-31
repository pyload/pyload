# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import sys
import time
import zipfile

from future import standard_library

from pyload.utils import debug
from pyload.utils.fs import makedirs
from pyload.utils.layer.safethreading import Thread

standard_library.install_aliases()


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
        self.__manager = manager  # Thread manager
        self.__pyload = manager.pyload_core
        self._ = self.__pyload._
        # Owner of the thread, every type should set it or overwrite user
        self.owner = owner

    @property
    def pyload_core(self):
        return self.__pyload

    @property
    def user(self):
        return self.owner.primary if self.owner else None

    @property
    def progress_info(self):
        return self.get_progress_info()

    def get_manager(self):
        return self.__manager

    def finished(self):
        """
        Remove thread from list.
        """
        self.__manager.remove_thread(self)

    def get_progress_info(self):
        """
        Retrieves progress information about the current running task

        :return: :class:`ProgressInfo`
        """
        pass

    def _gen_reports(self, file):
        si_entries = (
            ('pyload version', self.pyload_core.version),
            ('system platform', sys.platform),
            ('system version', sys.version),
            ('system encoding', sys.getdefaultencoding()),
            ('file-system encoding', sys.getfilesystemencoding()),
            ('current working directory', os.getcwd())
        )
        si_title = "SYSTEM INFO:"
        si_body = os.linesep.join(
            "\t{0:20} = {1}".format(name, value) for name, value in si_entries)
        sysinfo = os.linesep.join((si_title, si_body))

        # TODO: Add config setting dump
        reports = (
            ('traceback.txt', debug.format_traceback()),
            ('framestack.txt', debug.format_framestack()),
            ('plugindump.txt', debug.format_dump(file.plugin)),
            ('filedump.txt', debug.format_dump(file)),
            ('sysinfo.txt', sysinfo)
        )
        return reports

    def _zip(self, filepath, reports, dumpdir):
        filename = os.path.basename(filepath)
        with zipfile.ZipFile(filepath, 'wb') as zip:
            for fname in os.listdir(dumpdir):
                try:
                    arcname = os.path.join(filename, fname)
                    zip.write(os.path.join(dumpdir, fname), arcname)
                except Exception:
                    pass
            for fname, data in reports:
                arcname = os.path.join(filename, fname)
                zip.writestr(arcname, data)

    def debug_report(self, file):
        dumpdir = os.path.join(self.pyload_core.cachedir,
                               'plugins', file.pluginname)
        makedirs(dumpdir, exist_ok=True)

        # NOTE: Relpath to configdir
        reportdir = os.path.join('crashes', 'plugins', file.pluginname)
        makedirs(reportdir, exist_ok=True)

        filename = "debug-report_{0}_{1}.zip".format(
            file.pluginname, time.strftime("%d-%m-%Y_%H-%M-%S"))
        filepath = os.path.join(reportdir, filename)

        reports = self._gen_reports(file)
        self._zip(filepath, reports, dumpdir)

        self.pyload_core.log.info(
            self._('Debug Report written to file {0}').format(filename))
