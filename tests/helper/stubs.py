# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import builtins
import os
import sys
import time
from builtins import object
from logging import DEBUG, ERROR, INFO, WARN, log
from traceback import format_exc

from future import standard_library

from pyload.config import ConfigParser
from pyload.core import Core
from pyload.core.datatype import Role, User
from pyload.core.thread import PluginThread

standard_library.install_aliases()


# from pyload.core.inithomedir import init_dir
# init_dir(os.path.join("tests", "config"), True)

# Do nothing
def noop(*args, **kwargs):
    pass


class NoopClass(object):

    def __getattr__(self, item):
        return noop


ConfigParser.save = noop


class LogStub(object):

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
        Core.__init__(self)

        self.db.get_user_data = self.get_user_data
        self.log = LogStub()

    def get_server_version(self):
        return "TEST_RUNNER on {0}".format(time.strftime("%d %h %Y"))

    def init_logger(self, level):
        # init with empty logger
        self.log = NoopClass()

    def print_exc(self, force=False):
        log(ERROR, format_exc())

    def get_user_data(self, uid):
        if uid == 0:
            return admin_user
        elif uid == 1:
            return normal_user

        return other_user


class Thread(PluginThread):

    def __init__(self, core):
        PluginThread.__init__(self, core)
        self.plugin = None

    def debug_report(self):
        if hasattr(self, "file"):
            dump = PluginThread.debug_report(
                self, self.plugin.__name__, file=self.file)
        else:
            dump = PluginThread.debug_report(
                self, self.plugin.__name__, plugin=self.plugin)
        return dump


Core = TestCore

builtins._ = lambda x: x

admin_user = User(None, uid=0, role=Role.Admin)
normal_user = User(None, uid=1, role=Role.User)
other_user = User(None, uid=2, role=Role.User)

# fixes the module paths because we changed the directory
for name, m in sys.modules.items():
    if not name.startswith("tests") or not m or not hasattr(m, "__path__"):
        continue

    m.__path__[0] = os.path.join("..", "..", m.__path__[0])
