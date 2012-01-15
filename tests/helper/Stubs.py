# -*- coding: utf-8 -*-

import sys
from os.path import abspath, dirname, join
from time import strftime

sys.path.append(abspath(join(dirname(__file__), "..", "..", "module", "lib")))
sys.path.append(abspath(join(dirname(__file__), "..", "..")))

import __builtin__

from module.PyPackage import PyPackage
from module.threads.BaseThread import BaseThread
from module.config.ConfigParser import ConfigParser
from module.network.RequestFactory import RequestFactory
from module.plugins.PluginManager import PluginManager
from module.common.JsEngine import JsEngine

from logging import log, DEBUG, INFO, WARN, ERROR


# Do nothing
def noop(*args, **kwargs):
    pass

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


class NoLog:
    def debug(self, *args):
        pass

    def info(self, *args):
        pass

    def error(self, *args):
        log(ERROR, *args)

    def warning(self, *args):
        log(WARN, *args)


class Core:
    def __init__(self):
        self.log = NoLog()

        self.api = self
        self.core = self
        self.debug = True
        self.captcha = True
        self.config = ConfigParser()
        self.pluginManager = PluginManager(self)
        self.requestFactory = RequestFactory(self)
        __builtin__.pyreq = self.requestFactory
        self.accountManager = AccountManager()
        self.hookManager = self.eventManager = self.interActionManager = NoopClass()
        self.js = JsEngine()
        self.cache = {}
        self.packageCache = {}

        self.log = LogStub()

    def getServerVersion(self):
        return "TEST_RUNNER on %s" % strftime("%d %h %Y")

    def path(self, path):
        return path

    def updateLink(self, *args):
        pass

    def updatePackage(self, *args):
        pass

    def getPackage(self, id):
        return PyPackage(self, 0, "tmp", "tmp", "", "", 0, 0)


class NoopClass:
    def __getattr__(self, item):
        return noop

class AccountManager:

    def getAccountForPlugin(self, name):
        return None

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

__builtin__._ = lambda x: x
__builtin__.pypath = abspath(join(dirname(__file__), "..", ".."))
__builtin__.hookManager = NoopClass()
__builtin__.pyreq = None