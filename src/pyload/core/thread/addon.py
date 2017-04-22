# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from copy import copy
from traceback import print_exc

from future import standard_library
standard_library.install_aliases()

from ..datatype.init import ProgressInfo, ProgressType
from .plugin import PluginThread


class AddonThread(PluginThread):
    """
    Thread for addons.
    """
    __slots__ = ['_progressinfo', 'active', 'args', 'fn', 'kwargs']

    def __init__(self, manager, fn, args, kwargs):
        """
        Constructor.
        """
        PluginThread.__init__(self, manager)

        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.active = []
        self._progressinfo = None

        manager.add_thread(self)

        self.start()

    def get_active_files(self):
        return self.active

    def get_progress(self):
        """
        Progress of the thread.
        """
        if not self.active:
            return None
        active = self.active[0]
        return ProgressInfo(active.pluginname, active.name, active.get_status_name(), 0,
                            self._progressinfo, 100, self.owner, ProgressType.Addon)

    def add_active(self, file):
        """
        Adds a file to active list and thus will be displayed on overview.
        """
        if file not in self.active:
            self.active.append(file)

    def finish_file(self, file):
        if file in self.active:
            self.active.remove(file)

        file.finish_if_done()

    def run(self):  # TODO: approach via func_code
        try:
            try:
                self.kwargs['thread'] = self
                self.fn(*self.args, **self.kwargs)
            except TypeError as e:
                # dirty method to filter out exceptions
                if "unexpected keyword argument 'thread'" not in e.args[0]:
                    raise

                del self.kwargs['thread']
                self.fn(*self.args, **self.kwargs)
        except Exception as e:
            if hasattr(self.fn, "im_self"):
                addon = self.fn.__self__
                addon.log_error(_("An Error occurred"), str(e))
                if self.manager.pyload.debug:
                    print_exc()
                    # self.debug_report(addon.__name__, plugin=addon)

        finally:
            local = copy(self.active)
            for x in local:
                self.fninish_file(x)

            self.fninished()
