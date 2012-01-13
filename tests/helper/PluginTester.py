# -*- coding: utf-8 -*-

from unittest import TestCase
from os.path import abspath
from sys import exc_clear, exc_info
from logging import log, DEBUG
from time import sleep, time

from Stubs import Thread, Core, noop
from sys import stderr

from module.plugins.Hoster import Hoster, Abort, Fail

def _wait(self):
    """ waits the time previously set """
    self.waiting = True

    waittime = self.pyfile.waitUntil - time()
    log(DEBUG, "waiting %ss" % waittime)

    if self.wantReconnect:
        raise Fail("Would wait for reconnect %ss" % waittime )
    if self.wantReconnect or waittime > 300:
        raise Fail("Would wait %ss" % waittime )

    while self.pyfile.waitUntil > time():
        sleep(1)
        if self.pyfile.abort: raise Abort

    self.waiting = False
    self.pyfile.setStatus("starting")

Hoster.wait = _wait

Hoster.checkForSameFiles = noop

class PluginTester(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    def setUp(self):
        self.thread = Thread(self.core)
        exc_clear()

    def tearDown(self):
        exc = exc_info()
        if exc != (None, None, None):
            debug = self.thread.writeDebugReport()
            log(DEBUG, debug)
            # generate attachment
            stderr.write("\n[[ATTACHMENT|%s]]\n" % abspath(debug))