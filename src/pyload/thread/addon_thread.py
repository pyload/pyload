# -*- coding: utf-8 -*-
# @author: RaNaN, vuolter

import os
import pprint
import time
import traceback
from builtins import _, str
from copy import copy
from queue import Queue
from sys import exc_info
from threading import Thread
from types import MethodType

import pycurl
from pyload.api import OnlineStatus
from pyload.datatype.pyfile import PyFile
from pyload.plugins.plugin import Abort, Fail, Reconnect, Retry, SkipDownload
from pyload.utils.packagetools import parseNames
from pyload.thread.plugin_thread import PluginThread


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

        manager.localThreads.append(self)

        self.start()

    def getActiveFiles(self):
        return self.active

    def addActive(self, pyfile):
        """
        Adds a pyfile to active list and thus will be displayed on overview.
        """
        if pyfile not in self.active:
            self.active.append(pyfile)

    def finishFile(self, pyfile):
        if pyfile in self.active:
            self.active.remove(pyfile)

        pyfile.finishIfDone()

    def run(self):
        try:
            try:
                self.kwargs["thread"] = self
                self.f(*self.args, **self.kwargs)
            except TypeError as e:
                # dirty method to filter out exceptions
                if "unexpected keyword argument 'thread'" not in e.args[0]:
                    raise

                del self.kwargs["thread"]
                self.f(*self.args, **self.kwargs)
        finally:
            local = copy(self.active)
            for x in local:
                self.finishFile(x)

            self.m.localThreads.remove(self)
