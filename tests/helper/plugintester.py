# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

from contextlib import closing
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

from tests.helper.stubs import Thread, Core, noop

from pyload.network.request import get_request
from pyload.plugins.base import Abort, Fail
from pyload.plugins.hoster import Hoster

def _wait(self):
    """
    Waits the time previously set.
    """
    self.waiting = True

    waittime = self.pyfile.wait_until - time()
    log(DEBUG, "waiting {}s".format(waittime))

    if self.want_reconnect and waittime > 300:
        raise Fail("Would wait for reconnect {}s".format(waittime))
    elif waittime > 300:
        raise Fail("Would wait {}s".format(waittime))

    while self.pyfile.wait_until > time():
        sleep(1)
        if self.pyfile.abort:
            raise Abort

    self.waiting = False
    self.pyfile.set_status("starting")

Hoster.wait = _wait


def decryptCaptcha(self, url, get={}, post={}, cookies=False, forceuser=False, imgtype='jpg',
                   result_type='textual'):
    img = self.load(url, get=get, post=post, cookies=cookies)

    id = "{:.2f}".format(time())[-6:].replace(".", "")
    with open(join("tmp", "tmp_captcha_{}_{}.{}".format(self.__name__, id, imgtype)), "wb") as f:
        f.write(img)

    log(DEBUG, "Using ct for captcha")
    # put username and passkey into two lines in ct.conf
    conf = join(expanduser("~"), "ct.conf")
    if not exists(conf):
        raise Exception("CaptchaService config {} not found".format(conf))
        
    with open(conf, "rb") as f:
        with closing(get_request()) as req:
            #raise timeout threshold
            req.c.setopt(LOW_SPEED_TIME, 300)
            
            json = req.load("http://captchatrader.com/api/submit",
                post={"api_key": "9f65e7f381c3af2b076ea680ae96b0b7",
                      "username": f.readline().strip(),
                      "password": f.readline().strip(),
                      "value": (FORM_FILE, temp_file.name),
                      "type": "file"}, multipart=True)

    response = loads(json)
    log(DEBUG, str(response))
    result = response[1]

    self.c_task = response[0]

    return result

Hoster.decrypt_captcha = decryptCaptcha

def invalidCaptcha(self):
    log(DEBUG, "Captcha invalid")

Hoster.invalid_captcha = invalidCaptcha

def correctCaptcha(self):
    log(DEBUG, "Captcha correct")

Hoster.correct_captcha = correctCaptcha

Hoster.check_for_same_files = noop


class PluginTester(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        name = "{}.{}".format(cls.__module__, cls.__name__)
        for f in glob(join(name, "debug_*")):
            remove(f)

    # Copy debug report to attachment dir for jenkins
    @classmethod
    def tearDownClass(cls):
        name = "{}.{}".format(cls.__module__, cls.__name__)
        if not exists(name):
            makedirs(name)
        for f in glob("debug_*"):
            move(f, join(name, f))

    def setUp(self):
        self.thread = Thread(self.pyload)
        exc_clear()

    def tearDown(self):
        exc = exc_info()
        if exc != (None, None, None):
            debug = self.thread.write_debug_report()
            log(DEBUG, debug)
