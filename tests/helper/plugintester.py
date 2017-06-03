# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import shutil
import sys
import time
from builtins import str
from glob import glob
from json import loads
from logging import DEBUG, log

from future import standard_library

from pycurl import FORM_FILE, LOW_SPEED_TIME
from pyload.core.plugin.base import Abort, Fail
from pyload.core.plugin.hoster import Hoster
from pyload.requests import get_request
from pyload.utils.fs import lopen, makedirs, remove
from tests.helper.stubs import Core, Thread, noop
from unittest2 import TestCase

standard_library.install_aliases()


def _wait(self):
    """
    Waits the time previously set.
    """
    self.waiting = True

    waittime = self.file.wait_until - time.time()
    log(DEBUG, "waiting {0}s".format(waittime))

    if self.want_reconnect and waittime > 300:
        raise Fail("Would wait for reconnect {0}s".format(waittime))
    elif waittime > 300:
        raise Fail("Would wait {0}s".format(waittime))

    while self.file.wait_until > time.time():
        time.sleep(1)
        if self.file.abort:
            raise Abort

    self.waiting = False
    self.file.set_status("starting")


Hoster.wait = _wait


def decrypt_captcha(self, url, get={},
                    post={},
                    cookies=False, forceuser=False, imgtype='jpg',
                    result_type='textual'):
    img = self.load(url, get=get, post=post, cookies=cookies)

    id = "{0:.2f}".format(time.time())[-6:].replace(".", "")
    with lopen(os.path.join("tmp_captcha_{0}_{1}.{2}".format(self.__name__, id, imgtype)), mode='wb') as fp:
        fp.write(img)

    log(DEBUG, "Using ct for captcha")
    # put username and passkey into two lines in ct.conf
    conf = os.path.join(os.path.expanduser("~"), "ct.conf")
    if not os.path.exists(conf):
        raise Exception("CaptchaService config {0} not found".format(conf))

    with lopen(conf, mode='rb') as fp:
        with get_request() as req:  # TODO: Check get_request
            # raise timeout threshold
            req.c.setopt(LOW_SPEED_TIME, 300)

            json = req.load(
                "http://captchatrader.com/api/submit",
                post={'api_key': "9f65e7f381c3af2b076ea680ae96b0b7",
                      'username': fp.readline().strip(),
                      'password': fp.readline().strip(),
                      'value': (FORM_FILE, fp.name),
                      'type': "file"},
                multipart=True)

    response = loads(json)
    log(DEBUG, str(response))
    result = response[1]

    self.c_task = response[0]

    return result


Hoster.decrypt_captcha = decrypt_captcha


def invalid_captcha(self):
    log(DEBUG, "Captcha invalid")


Hoster.invalid_captcha = invalid_captcha


def correct_captcha(self):
    log(DEBUG, "Captcha correct")


Hoster.correct_captcha = correct_captcha

Hoster.check_for_same_files = noop


class PluginTester(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        name = "{0}.{1}".format(cls.__module__, cls.__name__)
        for fname in glob(os.path.join(name, "debug_*")):
            remove(fname, trash=True)

    # Copy debug report to attachment dir for jenkins
    @classmethod
    def tearDownClass(cls):
        name = "{0}.{1}".format(cls.__module__, cls.__name__)
        makedirs(name, exist_ok=True)
        for fname in glob("debug_*"):
            shutil.move(fname, os.path.join(name, fname))

    def setUp(self):
        self.thread = Thread(self.pyload)
        sys.exc_clear()

    def tearDown(self):
        exc = sys.exc_info()
        if exc != (None, None, None):
            debug = self.thread.debug_report()
            log(DEBUG, debug)
