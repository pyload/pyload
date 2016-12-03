# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import sys
from os.path import join
from time import strftime
from traceback import format_exc

import __builtin__

from pyload.InitHomeDir import init_dir

init_dir(join("tests", "config"), True)

from pyload.Api import Role
from pyload.Core import Core
from pyload.datatypes.User import User
from pyload.threads.BaseThread import BaseThread
from pyload.config.ConfigParser import ConfigParser

from logging import log, DEBUG, INFO, WARN, ERROR

# Do nothing
def noop(*args, **kwargs):
    pass


class NoopClass:
    def __getattr__(self, item):
        return noop


ConfigParser.save = noop


class LogStub:
    def debug(self, *args):
        log(DEBUG, *args)

    def info(self, *args):
        log(INFO, *args)

    def error(self, *args):
        log(ERROR, *args)

    def warning(self, *args):
        log(WARN, *args)


class TestCore(Core):
    def __init__(self):
        super(TestCore, self).__init__()
        self.start(tests=True)

        self.db.getUserData = self.getUserData
        self.log = LogStub()

    def getServerVersion(self):
        return "TEST_RUNNER on %s" % strftime("%d %h %Y")

    def init_logger(self, level):
        # init with empty logger
        self.log = NoopClass()

    def print_exc(self, force=False):
        log(ERROR, format_exc())

    def getUserData(self, uid):
        if uid == 0:
            return adminUser
        elif uid == 1:
            return normalUser

        return otherUser


class Thread(BaseThread):
    def __init__(self, core):
        BaseThread.__init__(self, core)
        self.plugin = None


    def writeDebugReport(self):
        if hasattr(self, "pyfile"):
            dump = BaseThread.writeDebugReport(self, self.plugin.__name__, pyfile=self.pyfile)
        else:
            dump = BaseThread.writeDebugReport(self, self.plugin.__name__, plugin=self.plugin)

        return dump


Core = TestCore

__builtin__._ = lambda x: x

adminUser = User(None, uid=0, role=Role.Admin)
normalUser = User(None, uid=1, role=Role.User)
otherUser = User(None, uid=2, role=Role.User)

# fixes the module paths because we changed the directory
for name, m in sys.modules.items():
    if not name.startswith("tests") or not m or not hasattr(m, "__path__"):
        continue

    m.__path__[0] = join("..", "..", m.__path__[0])
