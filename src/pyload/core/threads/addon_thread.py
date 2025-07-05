# -*- coding: utf-8 -*-

import inspect
from copy import copy

from .plugin_thread import PluginThread


class AddonThread(PluginThread):
    """
    thread for addons.
    """

    # ----------------------------------------------------------------------
    def __init__(self, manager, function, args, kwargs):
        """
        Constructor.
        """
        super().__init__(manager)

        self.f = function
        self.args = args
        self.kwargs = kwargs

        self.active = []

        manager.local_threads.append(self)

        self.start()

    def get_active_files(self):
        return self.active

    def add_active(self, pyfile):
        """
        Adds a pyfile to the active list and thus will be displayed on overview.
        """
        if pyfile not in self.active:
            self.active.append(pyfile)

    def finish_file(self, pyfile):
        if pyfile in self.active:
            self.active.remove(pyfile)

        pyfile.finish_if_done()

    def run(self):
        sig = inspect.signature(self.f)
        param_info = sig.parameters.get("thread")
        if param_info is not None and param_info.kind in (
            inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD
        ):
            self.kwargs["thread"] = self

        try:
            self.f(*self.args, **self.kwargs)

        finally:
            local = copy(self.active)
            for x in local:
                self.finish_file(x)

            self.m.local_threads.remove(self)
