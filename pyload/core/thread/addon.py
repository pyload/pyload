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
    __slots__ = ['active', 'args', 'fn', 'kwargs']

    def __init__(self, m, fn, args, kwargs):
        """
        Constructor.
        """
        PluginThread.__init__(self, m)

        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.active = []
        self.progress = 0

        m.add_thread(self)

        self.start()

    def get_active_files(self):
        return self.active

    # TODO: multiple progresses
    def set_progress(self, progress, pyfile=None):
        """
        Sets progress for the thread in percent.
        """
        self.progress = progress

    def get_progress(self):
        """
        Progress of the thread.
        """
        if self.active:
            active = self.active[0]
            return ProgressInfo(active.pluginname, active.name, active.get_status_name(), 0,
                                self.progress, 100, self.owner, ProgressType.Addon)

    def add_active(self, pyfile):
        """
        Adds a pyfile to active list and thus will be displayed on overview.
        """
        if pyfile not in self.active:
            self.active.append(pyfile)

    def finish_file(self, pyfile):
        if pyfile in self.active:
            self.active.remove(pyfile)

        pyfile.finish_if_done()

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
                addon.log_error(_("An Error occurred"), e.message)
                if self.manager.pyload.debug:
                    print_exc()
                    self.write_debug_report(addon.__name__, plugin=addon)

        finally:
            local = copy(self.active)
            for x in local:
                self.fninish_file(x)

            self.fninished()
