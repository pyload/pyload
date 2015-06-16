# -*- coding: utf-8 -*-

from __future__ import with_statement

import pycurl
import re

from base64 import b64encode

from module.network.RequestFactory import getRequest
from module.plugins.internal.Hook import Hook, threaded


class ImageTyperzException(Exception):

    def __init__(self, err):
        self.err = err


    def getCode(self):
        return self.err


    def __str__(self):
        return "<ImageTyperzException %s>" % self.err


    def __repr__(self):
        return "<ImageTyperzException %s>" % self.err


class ImageTyperz(Hook):
    __name__    = "ImageTyperz"
    __type__    = "hook"
    __version__ = "0.07"

    __config__ = [("username", "str", "Username", ""),
                  ("passkey", "password", "Password", ""),
                  ("force", "bool", "Force IT even if client is connected", False)]

    __description__ = """Send captchas to ImageTyperz.com"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"   , "RaNaN@pyload.org"   ),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    interval = 0  #@TODO: Remove in 0.4.10

    SUBMIT_URL = "http://captchatypers.com/Forms/UploadFileAndGetTextNEW.ashx"
    RESPOND_URL = "http://captchatypers.com/Forms/SetBadImage.ashx"
    GETCREDITS_URL = "http://captchatypers.com/Forms/RequestBalance.ashx"


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def getCredits(self):
        res = self.load(self.GETCREDITS_URL,
                     post={'action': "REQUESTBALANCE",
                           'username': self.getConfig('username'),
                           'password': self.getConfig('passkey')})

        if res.startswith('ERROR'):
            raise ImageTyperzException(res)

        try:
            balance = float(res)
        except Exception:
            raise ImageTyperzException("Invalid response")

        self.logInfo(_("Account balance: $%s left") % res)
        return balance


    def submit(self, captcha, captchaType="file", match=None):
        req = getRequest()
        #raise timeout threshold
        req.c.setopt(pycurl.LOW_SPEED_TIME, 80)

        try:
            #@NOTE: Workaround multipart-post bug in HTTPRequest.py
            if re.match("^\w*$", self.getConfig('passkey')):
                multipart = True
                data = (pycurl.FORM_FILE, captcha)
            else:
                multipart = False
                with open(captcha, 'rb') as f:
                    data = f.read()
                data = b64encode(data)

            res = self.load(self.SUBMIT_URL,
                            post={'action': "UPLOADCAPTCHA",
                                  'username': self.getConfig('username'),
                                  'password': self.getConfig('passkey'), "file": data},
                            multipart=multipart,
                            req=req)
        finally:
            req.close()

        if res.startswith("ERROR"):
            raise ImageTyperzException(res)
        else:
            data = res.split('|')
            if len(data) == 2:
                ticket, result = data
            else:
                raise ImageTyperzException("Unknown response: %s" % res)

        return ticket, result


    def captcha_task(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.getConfig('username') or not self.getConfig('passkey'):
            return False

        if self.core.isClientConnected() and not self.getConfig('force'):
            return False

        if self.getCredits() > 0:
            task.handler.append(self)
            task.data['service'] = self.__name__
            task.setWaiting(100)
            self._processCaptcha(task)

        else:
            self.logInfo(_("Your %s account has not enough credits") % self.__name__)


    def captcha_invalid(self, task):
        if task.data['service'] == self.__name__ and "ticket" in task.data:
            res = self.load(self.RESPOND_URL,
                         post={'action': "SETBADIMAGE",
                               'username': self.getConfig('username'),
                               'password': self.getConfig('passkey'),
                               'imageid': task.data['ticket']})

            if res == "SUCCESS":
                self.logInfo(_("Bad captcha solution received, requested refund"))
            else:
                self.logError(_("Bad captcha solution received, refund request failed"), res)


    @threaded
    def _processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except ImageTyperzException, e:
            task.error = e.getCode()
            return

        task.data['ticket'] = ticket
        task.setResult(result)
