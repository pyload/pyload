# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str
from unittest import TestCase
from os import makedirs, remove
from os.path import exists, join, expanduser
from shutil import move
from sys import exc_clear, exc_info
from logging import log, DEBUG
from time import sleep, time
from glob import glob

from pycurl import LOW_SPEED_TIME, FORM_FILE
from json import loads

from .Stubs import Thread, Core, noop

from pyload.network.RequestFactory import getRequest
from pyload.plugins.Base import Abort, Fail
from pyload.plugins.Hoster import Hoster

def _wait(self):
    """ waits the time previously set """
    self.waiting = True

    waittime = self.pyfile.waitUntil - time()
    log(DEBUG, "waiting %ss" % waittime)

    if self.wantReconnect and waittime > 300:
        raise Fail("Would wait for reconnect %ss" % waittime)
    elif waittime > 300:
        raise Fail("Would wait %ss" % waittime)

    while self.pyfile.waitUntil > time():
        sleep(1)
        if self.pyfile.abort: raise Abort

    self.waiting = False
    self.pyfile.setStatus("starting")

Hoster.wait = _wait


def decryptCaptcha(self, url, get={}, post={}, cookies=False, forceUser=False, imgtype='jpg',
                   result_type='textual'):
    img = self.load(url, get=get, post=post, cookies=cookies)

    id = ("%.2f" % time())[-6:].replace(".", "")
    temp_file = open(join("tmp", "tmpCaptcha_%s_%s.%s" % (self.__name__, id, imgtype)), "wb")
    temp_file.write(img)
    temp_file.close()

    log(DEBUG, "Using ct for captcha")
    # put username and passkey into two lines in ct.conf
    conf = join(expanduser("~"), "ct.conf")
    if not exists(conf):
        raise Exception("CaptchaService config %s not found." % conf)
    f = open(conf, "rb")
    req = getRequest()

    #raise timeout threshold
    req.c.setopt(LOW_SPEED_TIME, 300)

    try:
        json = req.load("http://captchatrader.com/api/submit",
            post={"api_key": "9f65e7f381c3af2b076ea680ae96b0b7",
                  "username": f.readline().strip(),
                  "password": f.readline().strip(),
                  "value": (FORM_FILE, temp_file.name),
                  "type": "file"}, multipart=True)
    finally:
        f.close()
        req.close()

    response = loads(json)
    log(DEBUG, str(response))
    result = response[1]

    self.cTask = response[0]

    return result

Hoster.decryptCaptcha = decryptCaptcha

def invalidCaptcha(self):
    log(DEBUG, "Captcha invalid")

Hoster.invalidCaptcha = invalidCaptcha

def correctCaptcha(self):
    log(DEBUG, "Captcha correct")

Hoster.correctCaptcha = correctCaptcha

Hoster.checkForSameFiles = noop


class PluginTester(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        name = "%s.%s" % (cls.__module__, cls.__name__)
        for f in glob(join(name, "debug_*")):
            remove(f)

    # Copy debug report to attachment dir for jenkins
    @classmethod
    def tearDownClass(cls):
        name = "%s.%s" % (cls.__module__, cls.__name__)
        if not exists(name): makedirs(name)
        for f in glob("debug_*"):
            move(f, join(name, f))

    def setUp(self):
        self.thread = Thread(self.core)
        exc_clear()

    def tearDown(self):
        exc = exc_info()
        if exc != (None, None, None):
            debug = self.thread.writeDebugReport()
            log(DEBUG, debug)
