# -*- coding: utf-8 -*-


from __future__ import absolute_import, unicode_literals

from copy import copy

from future import standard_library

from pyload.core.datatype.base import ProgressInfo, ProgressType
from pyload.core.thread.plugin import PluginThread

standard_library.install_aliases()


class AddonThread(PluginThread):
    """Thread for addons."""
    __slots__ = ['_progress', 'active', 'args', 'func', 'kwargs']

    def __init__(self, manager, func, args, kwargs):
        """Constructor."""
        super(AddonThread, self).__init__(manager)

        self.func = func
        self.args = args
        self.kwgs = kwargs

        self.active = []
        self.__progress_info = None  # ProgressInfo

    def start(self):
        self.manager.add_thread(self)
        PluginThread.start(self)

    def get_active_files(self):
        return self.active

    def get_progress_info(self):
        """Progress of the thread."""
        if not self.active:
            return
        active = self.active[0]
        return ProgressInfo(
            active.pluginname, active.name, active.get_status_name(), 0,
            self.__progress_info, 100, self.owner, ProgressType.Addon)

    def add_active(self, file):
        """Adds a file to active list and thus will be displayed on
        overview."""
        if file in self.active:
            return
        self.active.append(file)

    def finish_file(self, file):
        if file in self.active:
            self.active.remove(file)

        file.finish_if_done()

    def run(self):  # TODO: approach via func_code
        try:
            try:
                self.kwgs['thread'] = self
                self.func(*self.args, **self.kwgs)

            except TypeError as exc:
                # dirty method to filter out exceptions
                if "unexpected keyword argument 'thread'" not in exc.args[0]:
                    raise

                del self.kwgs['thread']
                self.func(*self.args, **self.kwgs)

        except Exception as exc:
            if hasattr(self.func, 'im_self'):
                addon = self.func.__self__
                addon.log_error(self._('An Error occurred'))
                self.pyload.log.error(exc, exc_info=self.pyload.debug)
                # if self.pyload.debug:
                # self.debug_report(addon.__name__, plugin=addon)

        finally:
            local = copy(self.active)
            for x in local:
                self.funcinish_file(x)

            self.funcinished()
